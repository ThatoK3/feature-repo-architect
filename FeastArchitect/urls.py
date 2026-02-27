"""
Feast Architect API URLs
All endpoints prefixed with /api/
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'repositories', views.FeastRepositoryViewSet, basename='repository')
router.register(r'datasources', views.DataSourceViewSet, basename='datasource')
router.register(r'entities', views.EntityViewSet, basename='entity')
router.register(r'audit-logs', views.AuditLogViewSet, basename='auditlog')
router.register(r'chats', views.LLMChatSessionViewSet, basename='chat')


urlpatterns = [
    path('api/', include(router.urls)),
    
    # UI rendering endpoint
    path('ui/feast', views.feast_architect_view, name='feast-architect'),
    # trailing slash version
    path('ui/feast/', views.feast_architect_view, name='feast-architect-slash'),
]


# API endpoints summary:
#
# Repositories:
#   GET    /api/repositories/              - List all repos
#   POST   /api/repositories/              - Create new repo
#   GET    /api/repositories/{id}/         - Get repo detail with JSON
#   PUT    /api/repositories/{id}/         - Update repo
#   DELETE /api/repositories/{id}/         - Delete repo
#   POST   /api/repositories/{id}/sync_datasources/  - Sync sources from JSON
#   POST   /api/repositories/{id}/export_json/         - Export as JSON
#   POST   /api/repositories/import_json/  - Import from JSON file
#
# Data Sources:
#   GET    /api/datasources/               - List sources (filter: ?repository=1)
#   POST   /api/datasources/               - Create source
#   GET    /api/datasources/{id}/          - Get source detail
#   PUT    /api/datasources/{id}/          - Update source
#   DELETE /api/datasources/{id}/          - Delete source
#
# Entities:
#   GET    /api/entities/                  - List entities
#   POST   /api/entities/                  - Create entity
#   GET    /api/entities/{id}/               - Get entity detail
#
# Audit Logs:
#   GET    /api/audit-logs/                - List user actions
#
# LLM Chats:
#   GET    /api/chats/                     - List active chats
#   POST   /api/chats/                     - Create new chat session
#   GET    /api/chats/{id}/                - Get chat with messages
#   POST   /api/chats/{id}/send_message/   - Send message to chat
#   POST   /api/chats/{id}/archive/        - Archive chat session
#   GET    /api/chats/history/             - Get chat history
