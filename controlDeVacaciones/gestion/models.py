from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum
from datetime import date, datetime 
# NOTA: Se ha eliminado la importación circular "from .models import Empleado, ...".

# Función auxiliar para calcular días base de vacaciones según LCT (Ley de Contrato de Trabajo, Argentina)
def calcular_dias_lct(antiguedad_anos):
    if antiguedad_anos <= 0.5: # Menos de 6 meses
        return 0 # Esto se debe manejar como 1 día cada 20 trabajados
    elif antiguedad_anos <= 5:
        return 14
    elif antiguedad_anos <= 10:
        return 21
    elif antiguedad_anos <= 20:
        return 28
    else:
        return 35

class Departamento(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    
    def __str__(self):
        return self.nombre

class Empleado(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    legajo = models.CharField(max_length=10, unique=True)
    dni = models.CharField(max_length=15, unique=True)
    nombre = models.CharField(max_length=50)
    apellido = models.CharField(max_length=50)
    departamento = models.ForeignKey(Departamento, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_ingreso = models.DateField()
    es_manager = models.BooleanField(default=False)
    jornada_estandar = models.DecimalField(max_digits=4, decimal_places=2, default=8.0) # Horas por día
    # Manager que aprueba sus solicitudes (opcional)
    manager_aprobador = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='empleados_a_cargo')
    primer_login = models.BooleanField(default=True, help_text="Indica si el usuario debe cambiar su contraseña en el próximo inicio de sesión.")

    def antiguedad_en_anos(self, fecha_referencia=None):
        """
        Calcula la antigüedad en años completos.
        Usa la fecha de hoy si no se proporciona una fecha de referencia.
        """
        if fecha_referencia is None:
            fecha_referencia = date.today()
            
        delta = fecha_referencia - self.fecha_ingreso
        return delta.days / 365.25

    def dias_base_lct(self, anio_ciclo):
        """Calcula los días de vacaciones base según LCT para un ciclo (basado en antigüedad al 31/12)"""
        fecha_corte = date(anio_ciclo, 12, 31)
        antiguedad = self.antiguedad_en_anos(fecha_corte)
        return calcular_dias_lct(antiguedad)
        
    def __str__(self):
        if self.user:
            return f"{self.apellido}, {self.nombre} ({self.user.username})"
        return f"{self.apellido}, {self.nombre}"
    


class SaldoVacaciones(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    ciclo = models.IntegerField()  # Año del ciclo
    dias_iniciales = models.IntegerField(default=0)
    dias_adicionales = models.IntegerField(default=0, null=True, blank=True)

    class Meta:
        unique_together = ('empleado', 'ciclo')

    def dias_consumidos_total(self):
        """Días de vacaciones consumidos en este ciclo."""
        consumido = RegistroVacaciones.objects.filter(
            empleado=self.empleado,
            fecha_inicio__year__gte=self.ciclo,
            estado='Aprobada'  # Solo contar solicitudes aprobadas
        ).aggregate(Sum('dias_solicitados'))['dias_solicitados__sum']
        
        return consumido or 0
    
    def dias_base_ciclo(self):
        """
        Días base del ciclo actual (sin incluir acumulados).
        Este valor se muestra en la columna "Disponible" del calendario.
        """
        dias_base_lct = self.empleado.dias_base_lct(self.ciclo)
        return max(self.dias_iniciales, dias_base_lct)
    
    def dias_acumulados_restantes(self):
        """
        Días acumulados que aún quedan después de consumir vacaciones.
        Los días consumidos se restan PRIMERO de los acumulados.
        Este valor se muestra en la columna "Acumuladas" del calendario.
        """
        dias_adicionales = self.dias_adicionales or 0
        dias_consumidos = self.dias_consumidos_total()
        
        # Restar primero de los acumulados (Permitir negativos)
        acumulados_restantes = dias_adicionales - dias_consumidos
        return acumulados_restantes

    def dias_totales(self):
        """
        Total de días que tiene derecho el empleado (base + acumulados).
        NO resta los días consumidos.
        """
        return self.dias_base_ciclo() + (self.dias_adicionales or 0)
    
    def total_disponible(self):
        """
        Días restantes después de restar los consumidos.
        Este valor se muestra en la columna "Restan" del calendario.
        Fórmula: dias_totales() - dias_consumidos_total()
        """
        return self.dias_totales() - self.dias_consumidos_total()

    @property
    def saldo_total(self):
        """
        Alias limpio para usar en el HTML.
        Es igual a total_disponible().
        """
        return self.total_disponible()
    def __str__(self):
        return f"Saldo de {self.empleado.apellido} para {self.ciclo}"

        
class DiasFestivos(models.Model):
    fecha = models.DateField(unique=True)
    descripcion = models.CharField(max_length=100)
    
    def __str__(self):
        return f"{self.fecha.strftime('%d/%m/%Y')} - {self.descripcion}"


class RegistroVacaciones(models.Model):
    ESTADO_PENDIENTE = 'Pendiente'
    ESTADO_APROBADA = 'Aprobada'
    ESTADO_RECHAZADA = 'Rechazada'
    ESTADO_CANCELADA = 'Cancelada'

    ESTADOS = [
        (ESTADO_PENDIENTE, 'Pendiente'),
        (ESTADO_APROBADA, 'Aprobada'),
        (ESTADO_RECHAZADA, 'Rechazada'),
        (ESTADO_CANCELADA, 'Cancelada'),
    ]

    empleado = models.ForeignKey('Empleado', on_delete=models.CASCADE)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    dias_solicitados = models.PositiveIntegerField(default=0)
    estado = models.CharField(max_length=20, choices=ESTADOS, default=ESTADO_PENDIENTE)
    razon = models.TextField(blank=True, null=True)
    fecha_solicitud = models.DateField(default=date.today)
    fecha_aprobacion = models.DateField(blank=True, null=True)
    manager_aprobador = models.ForeignKey(
        'Empleado',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='aprobaciones'
    )

    def calcular_dias_naturales(self):
        if self.fecha_inicio and self.fecha_fin:
            return max((self.fecha_fin - self.fecha_inicio).days + 1, 0)
        return 0

    def save(self, *args, **kwargs):
        self.dias_solicitados = self.calcular_dias_naturales()
        super().save(*args, **kwargs)

    def __str__(self):
        emp = self.empleado
        nombre = f"{emp.apellido}, {emp.nombre}"
        username = emp.user.username if emp.user else "Sin usuario"
        return f"{nombre} ({username}) - {self.fecha_inicio} a {self.fecha_fin} ({self.estado})"

    class Meta:
        verbose_name = "Registro de Vacaciones"
        verbose_name_plural = "Registros de Vacaciones"
        ordering = ['-fecha_solicitud']

    def es_aprobada(self):
        return self.estado == self.ESTADO_APROBADA

    def dias_restantes_para_inicio(self):
        return (self.fecha_inicio - date.today()).days

class ConfiguracionEmail(models.Model):
    # SMTP Settings
    email_host = models.CharField(max_length=200, default='mail.tudominio.com', help_text="Ej: mail.tudominio.com o cXXXX.ferozo.com")
    email_port = models.IntegerField(default=587)
    email_use_tls = models.BooleanField(default=True, verbose_name="Usar STARTTLS (Puerto 587)")
    email_use_ssl = models.BooleanField(default=False, verbose_name="Usar SSL Directo (Puerto 465)")
    email_host_user = models.CharField(max_length=200, help_text="Ej: info@tudominio.com")

    email_host_password = models.CharField(max_length=200, help_text="Contraseña de la cuenta de correo")

    
    # Destinatarios
    emails_notificacion = models.TextField(help_text="Emails separados por coma (,) que recibirán avisos de nuevas solicitudes.")
    
    # Activar/Desactivar
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"SMTP: {self.email_host_user}"

class Notificacion(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notificaciones')
    titulo = models.CharField(max_length=150)
    mensaje = models.TextField()
    leida = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    url = models.CharField(max_length=255, blank=True, null=True)
    solicitud = models.ForeignKey('RegistroVacaciones', on_delete=models.CASCADE, null=True, blank=True, related_name='notificaciones_sistema')

    class Meta:

        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"{self.titulo} - {self.usuario.username}"


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


# NOTA: Asegúrate de ejecutar 'python manage.py makemigrations' y luego 
# 'python manage.py migrate' después de guardar este archivo.