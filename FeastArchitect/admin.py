"""
Feast Architect Admin Configuration
"""
from django.contrib import admin
from .models import (
    FeastRepository, DataSource, Entity, 
    AuditLog, LLMChatSession, LLMMessage
)


@admin.register(FeastRepository)
class FeastRepositoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'location', 'default_owner', 'get_node_count', 'updated_at', 'created_by']
    list_filter = ['created_at', 'updated_at', 'default_owner']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'json_hash', 'last_synced_at']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'location', 'description', 'default_owner')
        }),
        ('Architecture Data', {
            'fields': ('architecture_json', 'settings', 'json_hash'),
            'classes': ('collapse',)
        }),
        ('Sync Info', {
            'fields': ('last_synced_at',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_node_count(self, obj):
        return obj.get_node_count()
    get_node_count.short_description = 'Nodes'


@admin.register(DataSource)
class DataSourceAdmin(admin.ModelAdmin):
    list_display = ['name', 'repository', 'kind', 'category', 'debezium_supported', 'owned_by', 'feast_connection_type']
    list_filter = ['kind', 'feast_connection_type', 'created_at', 'repository']
    search_fields = ['name', 'description', 'connection_string']
    readonly_fields = ['debezium_supported', 'category', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('repository', 'name', 'kind', 'description', 'tags')
        }),
        ('Ownership & Access', {
            'fields': ('owned_by', 'access_process'),
            'classes': ('collapse',)
        }),
        ('Connection', {
            'fields': ('connection_string', 'topic', 'feast_connection_type'),
            'classes': ('collapse',)
        }),
        ('Security', {
            'fields': ('column_security',),
            'classes': ('collapse',)
        }),
        ('Position', {
            'fields': ('pos_x', 'pos_y'),
            'classes': ('collapse',)
        }),
        ('Computed', {
            'fields': ('debezium_supported', 'category', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Entity)
class EntityAdmin(admin.ModelAdmin):
    list_display = ['name', 'repository', 'join_key', 'updated_at']
    list_filter = ['created_at', 'repository']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'user', 'action', 'resource_type', 'resource_name']
    list_filter = ['action', 'resource_type', 'timestamp']
    search_fields = ['resource_name', 'details']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'


class LLMMessageInline(admin.TabularInline):
    model = LLMMessage
    extra = 0
    readonly_fields = ['created_at', 'role', 'query_type', 'total_tokens']
    fields = ['role', 'content', 'query_type', 'total_tokens', 'created_at']
    can_delete = False
    max_num = 10  # Show last 10 messages


@admin.register(LLMChatSession)
class LLMChatSessionAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'repository', 'get_message_count', 'is_active', 'updated_at']
    list_filter = ['is_active', 'created_at', 'repository']
    search_fields = ['title', 'user__username']
    readonly_fields = ['created_at', 'updated_at', 'get_message_count']
    inlines = [LLMMessageInline]
    
    actions = ['archive_sessions']
    
    def archive_sessions(self, request, queryset):
        queryset.update(is_active=False)
    archive_sessions.short_description = "Archive selected sessions"


@admin.register(LLMMessage)
class LLMMessageAdmin(admin.ModelAdmin):
    list_display = ['session', 'role', 'query_type', 'total_tokens', 'created_at']
    list_filter = ['role', 'query_type', 'created_at']
    search_fields = ['content']
    readonly_fields = ['created_at', 'session']
