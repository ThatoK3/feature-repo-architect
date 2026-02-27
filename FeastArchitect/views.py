"""
DRF Views for Feast Architect API with hash-based conflict detection
"""
import hashlib
import json
import logging
from django.utils import timezone
from django.db import transaction
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend


from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from .models import (
    FeastRepository, DataSource, Entity,
    AuditLog, LLMChatSession, LLMMessage
)
from .serializers import (
    FeastRepositoryListSerializer, FeastRepositoryDetailSerializer,
    FeastRepositoryCreateUpdateSerializer, DataSourceSerializer,
    EntitySerializer, AuditLogSerializer, LLMChatSessionListSerializer,
    LLMChatSessionDetailSerializer, LLMChatCreateSerializer,
    LLMQuerySerializer, DataSourceSyncSerializer, LLMMessageSerializer
)
from .llm_client import GroqLLMClient, LLMContext

logger = logging.getLogger(__name__)


def compute_json_hash(data):
    """Compute MD5 hash of JSON data for conflict detection."""
    # Normalize: sort keys, ensure consistent formatting
    json_str = json.dumps(data, sort_keys=True, separators=(',', ':'))
    return hashlib.md5(json_str.encode('utf-8')).hexdigest()


class FeastRepositoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Feast repositories with hash-based conflict detection.
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'updated_at', 'name']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return FeastRepositoryListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return FeastRepositoryCreateUpdateSerializer
        return FeastRepositoryDetailSerializer
    
    def get_queryset(self):
        return FeastRepository.objects.filter(created_by=self.request.user)
    
    def _check_repository_exists(self, name, exclude_id=None):
        """Check if repository with name exists for this user."""
        queryset = self.get_queryset().filter(name=name)
        if exclude_id:
            queryset = queryset.exclude(id=exclude_id)
        return queryset.first()
    
    def _check_hash_conflict(self, instance, client_hash):
        """
        Check if client's hash matches server hash.
        Returns (has_conflict, server_hash, last_updated)
        """
        server_hash = instance.json_hash
        last_updated = instance.updated_at
        
        if not client_hash:
            return False, server_hash, last_updated
        
        # Normalize client hash (handle both full and partial JSON)
        if isinstance(client_hash, dict):
            client_hash = compute_json_hash(client_hash)
        
        has_conflict = server_hash != client_hash
        return has_conflict, server_hash, last_updated
    
    def create(self, request, *args, **kwargs):
        """Create with duplicate name check."""
        name = request.data.get('name')
        
        # Check for existing repo with same name
        existing = self._check_repository_exists(name)
        if existing:
            return Response({
                'error': 'Repository already exists',
                'detail': f'A repository named "{name}" already exists',
                'existing_id': existing.id,
                'existing_updated_at': existing.updated_at.isoformat(),
                'suggestion': 'Use PUT to update existing or choose a different name'
            }, status=status.HTTP_409_CONFLICT)
        
        # Compute initial hash if architecture provided
        if 'architecture_json' in request.data:
            arch = request.data['architecture_json']
            request.data['json_hash'] = compute_json_hash(arch)
        
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        """Update with hash-based conflict detection."""
        instance = self.get_object()
        
        # Check for name collision if renaming
        new_name = request.data.get('name')
        if new_name and new_name != instance.name:
            existing = self._check_repository_exists(new_name, exclude_id=instance.id)
            if existing:
                return Response({
                    'error': 'Name conflict',
                    'detail': f'Another repository named "{new_name}" already exists',
                    'existing_id': existing.id
                }, status=status.HTTP_409_CONFLICT)
        
        # Hash conflict detection
        client_hash = request.data.pop('client_hash', None)
        client_timestamp = request.data.pop('client_timestamp', None)
        
        if client_hash:
            has_conflict, server_hash, last_updated = self._check_hash_conflict(instance, client_hash)
            
            if has_conflict:
                return Response({
                    'error': 'Conflict detected',
                    'detail': 'Repository was modified by another session',
                    'server_hash': server_hash,
                    'client_hash': client_hash if isinstance(client_hash, str) else compute_json_hash(client_hash),
                    'last_updated': last_updated.isoformat(),
                    'your_timestamp': client_timestamp,
                    'resolution_options': [
                        'GET /api/repositories/{id}/ to fetch latest',
                        'PUT with force=true to overwrite',
                        'Revert your changes and reapply'
                    ]
                }, status=status.HTTP_409_CONFLICT)
        
        # Compute new hash if architecture changed
        if 'architecture_json' in request.data:
            arch = request.data['architecture_json']
            request.data['json_hash'] = compute_json_hash(arch)
            request.data['last_synced_at'] = timezone.now().isoformat()
        
        return super().update(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'])
    def force_update(self, request, pk=None):
        """
        Force update even if hash conflicts (admin/override).
        POST /api/repositories/{id}/force_update/
        """
        instance = self.get_object()
        
        # Skip hash check, just update
        if 'architecture_json' in request.data:
            arch = request.data['architecture_json']
            instance.architecture_json = arch
            instance.json_hash = compute_json_hash(arch)
            instance.last_synced_at = timezone.now()
            instance.save()
            
            # Log forced update
            AuditLog.objects.create(
                user=request.user,
                action='FORCE_UPDATE',
                resource_type='repository',
                resource_name=instance.name,
                details={'override': True}
            )
            
            return Response({
                'id': instance.id,
                'hash': instance.json_hash,
                'updated_at': instance.updated_at.isoformat(),
                'forced': True
            })
        
        return Response({'error': 'No architecture_json provided'}, status=400)
    
    @action(detail=True, methods=['get'])
    def check_status(self, request, pk=None):
        """
        Get repository status including hash for comparison.
        GET /api/repositories/{id}/check_status/
        """
        instance = self.get_object()
        
        # Get client's hash from query param
        client_hash = request.query_params.get('client_hash')
        
        response_data = {
            'id': instance.id,
            'name': instance.name,
            'exists': True,
            'last_updated': instance.updated_at.isoformat(),
            'server_hash': instance.json_hash,
            'last_synced_at': instance.last_synced_at.isoformat() if instance.last_synced_at else None,
            'node_count': instance.get_node_count(),
            'edge_count': instance.get_edge_count()
        }
        
        if client_hash:
            has_conflict = instance.json_hash != client_hash
            response_data['client_hash'] = client_hash
            response_data['hash_match'] = not has_conflict
            response_data['has_conflict'] = has_conflict
            response_data['status'] = 'conflict' if has_conflict else 'synced'
        else:
            response_data['status'] = 'unknown'  # No client hash to compare
        
        return Response(response_data)
    
    @action(detail=False, methods=['get'])
    def check_name(self, request):
        """
        Check if repository name exists without creating.
        GET /api/repositories/check_name/?name=my_repo
        """
        name = request.query_params.get('name')
        if not name:
            return Response({'error': 'name parameter required'}, status=400)
        
        existing = self._check_repository_exists(name)
        
        if existing:
            return Response({
                'exists': True,
                'name': name,
                'id': existing.id,
                'created_at': existing.created_at.isoformat(),
                'updated_at': existing.updated_at.isoformat(),
                'owner': existing.created_by.username if existing.created_by else None,
                'available': False
            })
        
        return Response({
            'exists': False,
            'name': name,
            'available': True
        })
    
    def perform_create(self, serializer):
        repo = serializer.save(created_by=self.request.user)
        
        # Compute and save hash
        if repo.architecture_json:
            repo.json_hash = compute_json_hash(repo.architecture_json)
            repo.last_synced_at = timezone.now()
            repo.save(update_fields=['json_hash', 'last_synced_at'])
        
        AuditLog.objects.create(
            user=self.request.user,
            action='CREATE',
            resource_type='repository',
            resource_name=repo.name,
            details={'hash': repo.json_hash}
        )
        return repo
    
    def perform_update(self, serializer):
        repo = serializer.save()
        
        # Update hash and sync time
        if 'architecture_json' in self.request.data:
            repo.json_hash = compute_json_hash(repo.architecture_json)
            repo.last_synced_at = timezone.now()
            repo.save(update_fields=['json_hash', 'last_synced_at'])
        
        AuditLog.objects.create(
            user=self.request.user,
            action='UPDATE',
            resource_type='repository',
            resource_name=repo.name,
            details={'hash': repo.json_hash}
        )
        return repo
    
    @action(detail=True, methods=['post'])
    def sync_datasources(self, request, pk=None):
        """Sync data sources with hash tracking."""
        repo = self.get_object()
        
        # Optional hash check
        client_hash = request.data.get('client_hash')
        if client_hash and client_hash != repo.json_hash:
            return Response({
                'error': 'Architecture changed since last sync',
                'server_hash': repo.json_hash,
                'client_hash': client_hash
            }, status=status.HTTP_409_CONFLICT)
        
        serializer = DataSourceSyncSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        sources_data = serializer.validated_data['sources']
        dry_run = serializer.validated_data.get('dry_run', False)
        
        results = {'created': [], 'updated': [], 'deleted': [], 'errors': []}
        existing = {ds.name: ds for ds in repo.data_sources.all()}
        incoming_names = set()
        
        for src in sources_data:
            name = src.get('name')
            if not name:
                results['errors'].append("Source missing name")
                continue
            
            incoming_names.add(name)
            
            data = {
                'kind': src.get('kind', 'postgres'),
                'owned_by': src.get('ownedBy', repo.default_owner),
                'access_process': src.get('accessProcess', ''),
                'connection_string': src.get('details', {}).get('connection', ''),
                'topic': src.get('details', {}).get('topic', ''),
                'description': src.get('description', ''),
                'tags': src.get('tags', []),
                'pos_x': src.get('x', 100),
                'pos_y': src.get('y', 100),
                'column_security': src.get('columnSecurity', {}),
                'feast_connection_type': self._infer_connection_type(src)
            }
            
            if name in existing:
                ds = existing[name]
                for key, value in data.items():
                    setattr(ds, key, value)
                if not dry_run:
                    ds.save()
                results['updated'].append(name)
            else:
                if not dry_run:
                    DataSource.objects.create(repository=repo, name=name, **data)
                results['created'].append(name)
        
        for name, ds in existing.items():
            if name not in incoming_names:
                if not dry_run:
                    ds.delete()
                results['deleted'].append(name)
        
        # After successful sync, update hash if architecture provided
        if not dry_run and 'architecture_json' in request.data:
            repo.architecture_json = request.data['architecture_json']
            repo.json_hash = compute_json_hash(repo.architecture_json)
            repo.last_synced_at = timezone.now()
            repo.save(update_fields=['architecture_json', 'json_hash', 'last_synced_at'])
        
        return Response({
            'dry_run': dry_run,
            'repository_id': repo.id,
            'results': results,
            'new_hash': repo.json_hash if not dry_run else None,
            'synced_at': repo.last_synced_at.isoformat() if not dry_run else None
        })
    
    def _infer_connection_type(self, src):
        """Infer Feast connection type from source config."""
        kind = src.get('kind', '')
        if kind == 'kafka':
            return 'stream'
        elif kind in ['dynamodb', 'redis']:
            return 'push'
        elif src.get('subtype') == 'on_demand':
            return 'request'
        return 'batch'
    
    @action(detail=True, methods=['post'])
    def export_json(self, request, pk=None):
        """Export with hash verification option."""
        repo = self.get_object()
        
        include_hash = request.query_params.get('include_hash', 'true').lower() == 'true'
        
        export_data = {
            'repository': {
                'id': repo.id,
                'name': repo.name,
                'location': repo.location,
                'default_owner': repo.default_owner,
                'settings': repo.settings
            },
            'export_date': timezone.now().isoformat(),
            'version': '3.0',
            'architecture': repo.architecture_json
        }
        
        if include_hash:
            export_data['server_hash'] = repo.json_hash
            export_data['last_updated'] = repo.updated_at.isoformat()
        
        AuditLog.objects.create(
            user=request.user,
            action='EXPORT',
            resource_type='repository',
            resource_name=repo.name,
            details={'hash': repo.json_hash}
        )
        
        return Response(export_data)
    
    @action(detail=False, methods=['post'])
    def import_json(self, request):
        """Import with duplicate detection and hash verification."""
        if 'file' not in request.FILES:
            return Response({'error': 'No file provided'}, status=400)
        
        file = request.FILES['file']
        try:
            data = json.loads(file.read())
        except json.JSONDecodeError as e:
            return Response({'error': f'Invalid JSON: {str(e)}'}, status=400)
        
        # Check for hash in imported file
        import_hash = data.get('server_hash') or data.get('hash')
        repo_data = data.get('repository', {})
        name = repo_data.get('name', 'Imported Repository')
        
        # Check for existing with same name
        existing = self._check_repository_exists(name)
        if existing:
            if import_hash and import_hash == existing.json_hash:
                return Response({
                    'error': 'Repository already exists with identical content',
                    'existing_id': existing.id,
                    'last_updated': existing.updated_at.isoformat(),
                    'suggestion': 'Use existing repository or rename import'
                }, status=status.HTTP_409_CONFLICT)
            
            return Response({
                'error': 'Repository name exists with different content',
                'existing_id': existing.id,
                'existing_hash': existing.json_hash,
                'import_hash': import_hash,
                'suggestion': 'Rename the import or update existing'
            }, status=status.HTTP_409_CONFLICT)
        
        # Create new
        with transaction.atomic():
            repo = FeastRepository.objects.create(
                name=name,
                location=repo_data.get('location', '/opt/feast/feature_repo'),
                default_owner=repo_data.get('default_owner', 'Data Platform Team'),
                settings=repo_data.get('settings', {}),
                architecture_json=data.get('architecture', {}),
                json_hash=import_hash or compute_json_hash(data.get('architecture', {})),
                last_synced_at=timezone.now(),
                created_by=request.user
            )
            
            # Create data sources from architecture
            nodes = data.get('architecture', {}).get('nodes', {})
            for node_id, node in nodes.items():
                if node.get('type') == 'datasource':
                    DataSource.objects.create(
                        repository=repo,
                        name=node.get('name', 'Unknown'),
                        kind=node.get('kind', 'postgres'),
                        owned_by=node.get('ownedBy', repo.default_owner),
                        access_process=node.get('accessProcess', ''),
                        description=node.get('description', ''),
                        tags=node.get('tags', []),
                        pos_x=node.get('x', 100),
                        pos_y=node.get('y', 100),
                        column_security=node.get('columnSecurity', {})
                    )
        
        AuditLog.objects.create(
            user=request.user,
            action='IMPORT',
            resource_type='repository',
            resource_name=repo.name,
            details={'hash': repo.json_hash}
        )
        
        return Response({
            'id': repo.id,
            'name': repo.name,
            'hash': repo.json_hash,
            'created': True
        }, status=201)


class DataSourceViewSet(viewsets.ModelViewSet):
    serializer_class = DataSourceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['kind', 'feast_connection_type', 'repository']
    search_fields = ['name', 'description', 'connection_string']
    
    def get_queryset(self):
        queryset = DataSource.objects.all()
        repo_id = self.request.query_params.get('repository')
        if repo_id:
            queryset = queryset.filter(repository_id=repo_id)
        return queryset.select_related('repository')


class EntityViewSet(viewsets.ModelViewSet):
    serializer_class = EntitySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['repository']
    search_fields = ['name', 'description']
    
    def get_queryset(self):
        queryset = Entity.objects.all()
        repo_id = self.request.query_params.get('repository')
        if repo_id:
            queryset = queryset.filter(repository_id=repo_id)
        return queryset.select_related('repository')


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['action', 'resource_type']
    ordering_fields = ['timestamp']
    
    def get_queryset(self):
        return AuditLog.objects.filter(user=self.request.user)


class LLMChatSessionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for LLM chat sessions with proper response handling.
    """
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return LLMChatSessionListSerializer
        elif self.action == 'create':
            return LLMChatCreateSerializer
        return LLMChatSessionDetailSerializer
    
    def get_queryset(self):
        return LLMChatSession.objects.filter(
            user=self.request.user,
            is_active=True
        ).select_related('repository')
    
    def create(self, request, *args, **kwargs):
        """Override create to handle initial LLM message."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            session = self.perform_create(serializer)
            
            # Re-fetch with messages for response
            session.refresh_from_db()
            response_serializer = LLMChatSessionDetailSerializer(session)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Failed to create chat session: {str(e)}")
            return Response(
                {'error': 'Failed to create chat', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def perform_create(self, serializer):
        """Create new chat session with optional initial message."""
        validated = serializer.validated_data
        
        # Get repository if specified
        repo = None
        repo_id = validated.get('repository_id')
        if repo_id:
            try:
                repo = FeastRepository.objects.get(
                    id=repo_id, 
                    created_by=self.request.user
                )
            except FeastRepository.DoesNotExist:
                logger.warning(f"Repository {repo_id} not found for chat")
        
        # Build context from repository
        context = {}
        if repo:
            context = {
                'repo_name': repo.name,
                'node_count': repo.get_node_count(),
                'edge_count': repo.get_edge_count()
            }
        
        # Create session
        session = LLMChatSession.objects.create(
            user=self.request.user,
            repository=repo,
            title=validated.get('title', 'New Chat'),
            context_json=context
        )
        
        # Handle initial message
        initial_msg = validated.get('initial_message', '')
        if initial_msg:
            try:
                self._send_to_llm(session, initial_msg, validated.get('query_type', 'default'))
            except Exception as e:
                logger.error(f"LLM initial message failed: {str(e)}")
                # Don't fail session creation, just log the error
                LLMMessage.objects.create(
                    session=session,
                    role='system',
                    content=f'Error initializing LLM: {str(e)}. Please try sending a message manually.',
                    query_type='error'
                )
        
        return session
    
    def _send_to_llm(self, session, message, query_type):
        """
        Send message to Groq and save response.
        Returns the result dict for API responses.
        """
        # Save user message
        user_msg = LLMMessage.objects.create(
            session=session,
            role='user',
            content=message,
            query_type=query_type
        )
        
        # Build context
        context = LLMContext(
            repo_name=session.context_json.get('repo_name', 'Unknown'),
            node_count=session.context_json.get('node_count', 0),
            edge_count=session.context_json.get('edge_count', 0)
        )
        
        # Call LLM
        try:
            client = GroqLLMClient()
            result = client.query(
                message=message,
                context=context,
                query_type=query_type,
                stream=False
            )
            
            # Save assistant response
            assistant_msg = LLMMessage.objects.create(
                session=session,
                role='assistant',
                content=result['response'],
                query_type=query_type,
                prompt_tokens=result['usage']['prompt_tokens'],
                completion_tokens=result['usage']['completion_tokens'],
                total_tokens=result['usage']['total_tokens'],
                model=result['model']
            )
            
            # Update session timestamp
            session.save(update_fields=['updated_at'])
            
            logger.info(f"LLM response saved: session={session.id}, tokens={result['usage']['total_tokens']}")
            
            return result
            
        except Exception as e:
            logger.error(f"LLM query failed: {str(e)}")
            
            # Save error as system message
            LLMMessage.objects.create(
                session=session,
                role='system',
                content=f'Error: {str(e)}',
                query_type='error'
            )
            raise
    
    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        """
        Send message to existing chat session.
        POST /api/chats/{id}/send_message/
        """
        session = self.get_object()
        serializer = LLMQuerySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            result = self._send_to_llm(
                session,
                serializer.validated_data['message'],
                serializer.validated_data.get('query_type', 'default')
            )
            
            # Return just the response data (not full session)
            return Response({
                'success': True,
                'response': result['response'],
                'usage': result['usage'],
                'model': result['model'],
                'query_type': result['query_type'],
                'session_id': session.id,
                'message_count': session.messages.count()
            })
            
        except Exception as e:
            logger.error(f"send_message failed: {str(e)}")
            return Response(
                {
                    'success': False,
                    'error': str(e),
                    'detail': 'LLM service unavailable. Please try again later.'
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
    
    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """Archive (soft delete) chat session."""
        session = self.get_object()
        session.is_active = False
        session.save(update_fields=['is_active', 'updated_at'])
        return Response({'status': 'archived', 'session_id': session.id})
    
    @action(detail=False, methods=['get'])
    def history(self, request):
        """Get chat history for current user."""
        sessions = self.get_queryset()[:50]
        serializer = LLMChatSessionListSerializer(sessions, many=True)
        return Response(serializer.data)




@login_required
def feast_architect_view(request):
    """
    Render the Feast Architect HTML template.
    URL: /ui/feast?repo_id=<id> or /ui/feast for new repo
    """
    repo_id = request.GET.get('repo_id')
    
    context = {
        'repo_id': repo_id,
        'user': request.user,
        'api_base_url': '/api'
    }
    
    # If repo_id provided, verify access and add repo info to context
    if repo_id:
        try:
            repo = FeastRepository.objects.get(id=repo_id, created_by=request.user)
            context['repo_name'] = repo.name
            context['repo_description'] = repo.description
        except FeastRepository.DoesNotExist:
            # Repo not found or not owned by user - will be handled by frontend
            context['repo_error'] = 'Repository not found or access denied'
    
    return render(request, 'FeastArchitect/architect.html', context)





