from django.shortcuts import render, get_object_or_404, redirect
from detection.models import Device, Detection, PestType
from detection.InsectDetector import InsectDetector
import requests
from django.http import Http404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordChangeForm
from django.contrib.auth import login as auth_login, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib import messages
from django import forms
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
import json
from django.core.paginator import Paginator
from django.db.models.functions import TruncHour, TruncDay, TruncMonth

@login_required
@permission_required('auth.view_dashboard', raise_exception=True)
def overview(request):
    total_devices = Device.objects.filter(is_deleted=False).count()
    total_logs = Detection.objects.count()
    # Get recent logs with device and pest type information
    recent_logs = Detection.objects.select_related(
        'image__device', 'pest_type'
    ).filter(
        image__device__is_deleted=False
    ).order_by('-created_at')[:10]
    
    # Get time range filter from GET params
    selected_range = request.GET.get('range', 'daily')

    # Get all pest types
    pest_types = list(PestType.objects.all())
    pest_type_names = [pt.name for pt in pest_types]

    # Prepare chart labels and date list based on range
    now = timezone.now()
    chart_labels = []
    date_list = []
    if selected_range == 'hourly':
        # Last 24 hours
        start = now - timedelta(hours=23)
        for i in range(24):
            dt = (start + timedelta(hours=i)).replace(minute=0, second=0, microsecond=0)
            chart_labels.append(dt.strftime('%H:00'))
            date_list.append(dt)
        trunc = TruncHour('created_at', tzinfo=timezone.get_current_timezone())
        group_by = 'hour'
    elif selected_range == 'monthly':
        # Last 12 months
        months = []
        y, m = now.year, now.month
        for _ in range(12):
            months.append((y, m))
            m -= 1
            if m == 0:
                m = 12
                y -= 1
        months.reverse()
        for y, m in months:
            dt = timezone.datetime(y, m, 1, tzinfo=timezone.get_current_timezone())
            chart_labels.append(dt.strftime('%b %Y'))
            date_list.append(dt)
        trunc = TruncMonth('created_at', tzinfo=timezone.get_current_timezone())
        group_by = 'month'
    elif selected_range == 'all':
        # All time, group by month
        first = Detection.objects.order_by('created_at').first()
        if first:
            start = first.created_at.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            months = []
            while start <= end:
                months.append(start)
                chart_labels.append(start.strftime('%b %Y'))
                start = (start + timedelta(days=32)).replace(day=1)
            date_list = months
        else:
            chart_labels = []
            date_list = []
        trunc = TruncMonth('created_at', tzinfo=timezone.get_current_timezone())
        group_by = 'month'
    else:
        # Default: daily, last 30 days
        end_date = now.date()
        start_date = end_date - timedelta(days=29)
        current_date = start_date
        while current_date <= end_date:
            chart_labels.append(current_date.strftime('%b %d'))
            date_list.append(current_date)
            current_date += timedelta(days=1)
        trunc = TruncDay('created_at', tzinfo=timezone.get_current_timezone())
        group_by = 'day'

    # Prepare a dataset for each pest type
    chart_datasets = []
    color_palette = [
        'rgb(75, 192, 192)', 'rgb(255, 99, 132)', 'rgb(255, 205, 86)',
        'rgb(54, 162, 235)', 'rgb(153, 102, 255)', 'rgb(255, 159, 64)',
        'rgb(201, 203, 207)', 'rgb(0, 200, 83)', 'rgb(255, 87, 34)',
        'rgb(121, 85, 72)', 'rgb(233, 30, 99)', 'rgb(63, 81, 181)'
    ]
    for idx, pest_type in enumerate(pest_types):
        # Get logs for this pest type and range
        qs = Detection.objects.filter(
            image__device__is_deleted=False,
            pest_type=pest_type
        )
        if selected_range == 'hourly':
            qs = qs.filter(created_at__gte=now - timedelta(hours=23))
        elif selected_range == 'monthly':
            qs = qs.filter(created_at__gte=now - timedelta(days=365))
        # For 'all', no filter
        elif selected_range == 'daily':
            qs = qs.filter(created_at__date__gte=now.date() - timedelta(days=29))
        # Group and count
        daily_logs = qs.annotate(period=trunc).values('period').annotate(count=Count('id')).order_by('period')
        date_to_count = {}
        for item in daily_logs:
            key = item['period']
            if group_by == 'hour':
                key = key.replace(minute=0, second=0, microsecond=0)
            elif group_by == 'day':
                key = key.date()
            elif group_by == 'month':
                key = key.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            date_to_count[key] = item['count']
        data = [date_to_count.get(dt, 0) for dt in date_list]
        chart_datasets.append({
            'label': pest_type.name,
            'data': data,
            'borderColor': color_palette[idx % len(color_palette)],
            'backgroundColor': color_palette[idx % len(color_palette)],
            'borderWidth': 3,
            'fill': False,
            'tension': 0.4,
            'pointBackgroundColor': color_palette[idx % len(color_palette)],
            'pointBorderColor': '#fff',
            'pointBorderWidth': 2,
            'pointRadius': 5,
            'pointHoverRadius': 7
        })

    # If no pest types or no data, show a message in the chart
    if not chart_datasets or all(all(v == 0 for v in ds['data']) for ds in chart_datasets):
        chart_labels = ['No Data']
        chart_datasets = [{
            'label': 'No Data',
            'data': [0],
            'borderColor': 'rgb(200,200,200)',
            'backgroundColor': 'rgb(200,200,200)',
            'borderWidth': 3,
            'fill': False,
            'tension': 0.4,
            'pointBackgroundColor': 'rgb(200,200,200)',
            'pointBorderColor': '#fff',
            'pointBorderWidth': 2,
            'pointRadius': 5,
            'pointHoverRadius': 7
        }]

    # Now chart_datasets is defined, so assign pest_type_totals
    pest_type_totals = {pt.name: sum(ds['data']) for pt, ds in zip(pest_types, chart_datasets)}

    return render(request, 'dashboard/overview.html', {
        'total_devices': total_devices,
        'total_logs': total_logs,
        'recent_logs': recent_logs,
        'chart_labels': json.dumps(chart_labels),
        'chart_datasets': json.dumps(chart_datasets),
        'pest_type_names': pest_type_names,
        'pest_type_totals': pest_type_totals,
        'selected_range': selected_range,
    })

@login_required
@permission_required('auth.view_dashboard', raise_exception=True)
def device_list(request):
    devices = Device.objects.filter(is_deleted=False).order_by('id')
    return render(request, 'dashboard/device_list.html', {'devices': devices})

@login_required
@permission_required('auth.edit_device', raise_exception=True)
def add_device(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
        
        if name and latitude and longitude:
            device = Device.objects.create(
                name=name,
                latitude=latitude,
                longitude=longitude,
                status=True,
                is_deleted=False
            )
            return redirect('device_detail', device_id=device.id)
    
    return render(request, 'dashboard/add_device.html')

@login_required
@permission_required('auth.delete_device', raise_exception=True)
def delete_device(request, device_id):
    device = get_object_or_404(Device, id=device_id)
    if request.method == 'POST':
        device.is_deleted = True
        device.save()
        return redirect('device_list')
    return redirect('device_detail', device_id=device.id)

@login_required
@permission_required('auth.view_device_list', raise_exception=True)
def device_detail(request, device_id):
    device = get_object_or_404(Device, id=device_id)
    if device.is_deleted:
        raise Http404()
    if request.method == 'POST':
        device.name = request.POST.get('name')
        device.latitude = request.POST.get('latitude')
        device.longitude = request.POST.get('longitude')
        # Update status from checkbox
        device.status = bool(request.POST.get('status'))
        device.save()
        return redirect('device_list')
    images = device.images.order_by('-created_at')
    paginator = Paginator(images, 5)  # Show 5 images per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'dashboard/device_detail.html', {
        'device': device,
        'page_obj': page_obj
    })

@login_required
@permission_required('auth.view_device_list', raise_exception=True)
def recover_devices(request):
    devices = Device.objects.filter(is_deleted=True).order_by('id')
    return render(request, 'dashboard/recover_device_list.html', {'devices': devices})

@login_required
@permission_required('auth.edit_device', raise_exception=True)
def recover_device(request):
    if request.method == 'POST':
        device_id = request.POST.get('device_id')
        if device_id:
            device = get_object_or_404(Device, id=device_id, is_deleted=True)
            device.is_deleted = False
            device.save()
    return redirect('recover_devices')

def detect_insect_upload(request):
    detection_result = None
    annotated_image_url = None
    original_url = None
    error = None
    selected_model = 'yolov11s'  # Default model
    
    if request.method == 'POST' and request.FILES.get('image'):
        image = request.FILES['image']
        selected_model = request.POST.get('model', 'yolov11s')
        try:
            response = requests.post(
                request.build_absolute_uri('/detection/api/detect-insect/'),
                files={'image': image},
                data={'model': selected_model}
            )
            if response.status_code == 200:
                data = response.json()
                detection_result = data.get('detections', [])
                annotated_image_url = data.get('annotated_image_url')
                original_url = data.get('original_image_url')
            else:
                error = response.json().get('error', 'Detection failed')
        except Exception as e:
            error = str(e)
    
    # Get available models for dropdown
    available_models = InsectDetector.get_available_models()
    
    return render(request, 'dashboard/detect_insect_upload.html', {
        'detection_result': detection_result,
        'annotated_image_url': annotated_image_url,
        'original_image_url': original_url,
        'error': error,
        'available_models': available_models,
        'selected_model': selected_model
    })

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return redirect('overview')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

@login_required
def profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProfileForm(instance=request.user)
    
    return render(request, 'dashboard/profile.html', {'form': form})

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed successfully!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordChangeForm(request.user)
    
    # Add Bootstrap classes to form fields
    for field in form.fields.values():
        field.widget.attrs.update({'class': 'form-control'})
    
    return render(request, 'dashboard/change_password.html', {'form': form})
