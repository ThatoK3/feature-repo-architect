"""
DRF Serializers for Feast Architect
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    FeastRepository, DataSource, Entity,
    AuditLog, LLMChatSession, LLMMessage
)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class DataSourceSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source='category', read_only=True)
    debezium_supported = serializers.BooleanField(source='debezium_supported', read_only=True)
    icon = serializers.SerializerMethodField()
    
    class Meta:
        model = DataSource
        fields = [
            'id', 'name', 'kind', 'category', 'debezium_supported',
            'owned_by', 'access_process', 'connection_string', 'topic',
            'feast_connection_type', 'description', 'tags',
            'pos_x', 'pos_y', 'column_security', 'icon',
            'created_at', 'updated_at'
        ]
    
    def get_icon(self, obj):
        icons = {
            'postgres': '🐘', 'mysql': '🐬', 'sqlserver': '🗃️', 
            'oracle': '🏛️', 'sqlite': '🪶', 'mongodb': '🍃',
            'dynamodb': '⚡', 'cassandra': '🔱', 'couchbase': '🛋️',
            'elasticsearch': '🔍', 'snowflake': '❄️', 'bigquery': '📊',
            'redshift': '🔺', 'databricks': '🧱', 'synapse': '🔷',
            'kafka': '📨', 'kinesis': '💧', 'pulsar': '⭐',
            'eventhubs': '🎯', 's3': '🪣', 'gcs': '☁️',
            'azureblob': '🔵', 'minio': '🪣', 'redis': '🔴',
            'memcached': '🧠', 'dragonfly': '🐉', 'neo4j': '🕸️',
            'neptune': '🌊', 'influxdb': '📈', 'timescaledb': '⏱️',
            'clickhouse': '🖱️', 'couchdb': '🛋️', 'rethinkdb': '🤔',
            'firebase': '🔥', 'supabase': '⚡'
        }
        return icons.get(obj.kind, '🗄️')


class EntitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Entity
        fields = [
            'id', 'name', 'join_key', 'description', 'tags',
            'pos_x', 'pos_y', 'created_at', 'updated_at'
        ]


class FeastRepositoryListSerializer(serializers.ModelSerializer):
    node_count = serializers.IntegerField(source='get_node_count', read_only=True)
    edge_count = serializers.IntegerField(source='get_edge_count', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = FeastRepository
        fields = [
            'id', 'name', 'location', 'description', 'default_owner',
            'node_count', 'edge_count', 'created_by_username',
            'created_at', 'updated_at'
        ]


class FeastRepositoryDetailSerializer(serializers.ModelSerializer):
    data_sources = DataSourceSerializer(many=True, read_only=True)
    entities = EntitySerializer(many=True, read_only=True)
    node_count = serializers.IntegerField(source='get_node_count', read_only=True)
    edge_count = serializers.IntegerField(source='get_edge_count', read_only=True)
    created_by = UserSerializer(read_only=True)
    
    class Meta:
        model = FeastRepository
        fields = [
            'id', 'name', 'location', 'description', 'default_owner',
            'architecture_json', 'settings', 'data_sources', 'entities',
            'node_count', 'edge_count', 'json_hash', 'last_synced_at',
            'created_by', 'created_at', 'updated_at'
        ]


class FeastRepositoryCreateUpdateSerializer(serializers.ModelSerializer):
    """For creating/updating - accepts architecture_json from frontend."""
    
    class Meta:
        model = FeastRepository
        fields = ['name', 'location', 'description', 'default_owner', 'architecture_json', 'settings']
    
    def validate_architecture_json(self, value):
        """Ensure valid JSON structure."""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Architecture must be a JSON object")
        return value


class AuditLogSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = [
            'id', 'timestamp', 'user_username', 'action', 
            'resource_type', 'resource_name', 'details', 'ip_address'
        ]


class LLMMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = LLMMessage
        fields = [
            'id', 'role', 'content', 'query_type',
            'prompt_tokens', 'completion_tokens', 'total_tokens',
            'model', 'created_at'
        ]


class LLMChatSessionListSerializer(serializers.ModelSerializer):
    message_count = serializers.IntegerField(source='get_message_count', read_only=True)
    repository_name = serializers.CharField(source='repository.name', read_only=True)
    
    class Meta:
        model = LLMChatSession
        fields = [
            'id', 'title', 'repository_name', 'message_count',
            'is_active', 'created_at', 'updated_at'
        ]


class LLMChatSessionDetailSerializer(serializers.ModelSerializer):
    messages = LLMMessageSerializer(many=True, read_only=True)
    repository = FeastRepositoryListSerializer(read_only=True)
    
    class Meta:
        model = LLMChatSession
        fields = [
            'id', 'title', 'repository', 'context_json',
            'messages', 'is_active', 'created_at', 'updated_at'
        ]


class LLMChatCreateSerializer(serializers.Serializer):
    """For creating new chat sessions."""
    repository_id = serializers.IntegerField(required=False, allow_null=True)
    title = serializers.CharField(max_length=255, default="New Chat")
    initial_message = serializers.CharField(required=False, allow_blank=True)
    query_type = serializers.CharField(default="default")


class LLMQuerySerializer(serializers.Serializer):
    """For sending messages to LLM."""
    message = serializers.CharField(required=True)
    query_type = serializers.CharField(default="default")
    stream = serializers.BooleanField(default=False)


class DataSourceSyncSerializer(serializers.Serializer):
    """For syncing data sources from JSON."""
    sources = serializers.ListField(child=serializers.DictField())
    dry_run = serializers.BooleanField(default=False, help_text="Preview changes without saving")
