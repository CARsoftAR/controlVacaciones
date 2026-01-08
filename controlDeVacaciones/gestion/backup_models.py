# gestion/models.py - Agregar al final del archivo

from django.db import models
from django.contrib.auth.models import User

# ... (tus modelos existentes) ...

class Backup(models.Model):
    """Modelo para registrar los backups realizados"""
    TIPO_CHOICES = [
        ('db', 'Base de Datos'),
        ('code', 'Código Fuente'),
        ('full', 'Completo'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('processing', 'Procesando'),
        ('completed', 'Completado'),
        ('failed', 'Fallido'),
    ]
    
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    archivo = models.CharField(max_length=500, blank=True)
    tamaño = models.BigIntegerField(default=0, help_text='Tamaño en bytes')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    mensaje_error = models.TextField(blank=True)
    commit_hash = models.CharField(max_length=100, blank=True, help_text='Hash del commit de Git')
    
    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = 'Backup'
        verbose_name_plural = 'Backups'
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.fecha_creacion.strftime('%Y-%m-%d %H:%M')}"
    
    @property
    def tamaño_mb(self):
        """Retorna el tamaño en MB"""
        return round(self.tamaño / (1024 * 1024), 2)
