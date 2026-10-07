from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import BodegaForm, VinoForm
from .models import Bodega, Categoria, Compra, ItemCompra, Varietal, Vino
from usuarios.models import CustomUser
from django.contrib import messages


def home(request):
    return render(request, 'vinoteca/home.html')


@login_required
def lista_vinos(request):
    vinos = Vino.objects.select_related('bodega', 'varietal', 'categoria')
    return render(request, 'vinoteca/lista_vinos.html', {'vinos': vinos})


@login_required
def detalle_vino(request, pk):
    vino = get_object_or_404(
        Vino.objects.select_related('bodega', 'varietal', 'categoria'),
        pk=pk,
    )
    return render(request, 'vinoteca/detalle_vino.html', {'vino': vino})


@login_required
@permission_required('vinoteca.add_vino', raise_exception=True)
def crear_vino(request):
    if request.method == 'POST':
        form = VinoForm(request.POST, request.FILES)
        if form.is_valid():
            vino = form.save()
            return redirect('detalle_vino', pk=vino.pk)
    else:
        form = VinoForm()
    return render(request, 'vinoteca/crear_vino.html', {'form': form})


@login_required
@permission_required('vinoteca.change_vino', raise_exception=True)
def editar_vino(request, pk):
    vino = get_object_or_404(Vino, pk=pk)
    if request.method == 'POST':
        form = VinoForm(request.POST, request.FILES, instance=vino)
        if form.is_valid():
            form.save()
            return redirect('detalle_vino', pk=pk)
    else:
        form = VinoForm(instance=vino)
    return render(request, 'vinoteca/editar_vino.html', {'form': form, 'vino': vino})


@login_required
@permission_required('vinoteca.delete_vino', raise_exception=True)
def eliminar_vino(request, pk):
    vino = get_object_or_404(Vino, pk=pk)
    if request.method == 'POST':
        vino.delete()
        return redirect('lista_vinos')
    return render(request, 'vinoteca/eliminar_vino.html', {'vino': vino})


@login_required
def lista_bodegas(request):
    bodegas = Bodega.objects.all()
    return render(request, 'vinoteca/lista_bodegas.html', {'bodegas': bodegas})


@login_required
def detalle_bodega(request, pk):
    bodega = get_object_or_404(Bodega, pk=pk)
    return render(request, 'vinoteca/detalle_bodega.html', {'bodega': bodega})


@login_required
@permission_required('vinoteca.add_bodega', raise_exception=True)
def crear_bodega(request):
    if request.method == 'POST':
        form = BodegaForm(request.POST, request.FILES)
        if form.is_valid():
            bodega = form.save()
            return redirect('detalle_bodega', pk=bodega.pk)
    else:
        form = BodegaForm()
    return render(request, 'vinoteca/crear_bodega.html', {'form': form})


@login_required
@permission_required('vinoteca.change_bodega', raise_exception=True)
def editar_bodega(request, pk):
    bodega = get_object_or_404(Bodega, pk=pk)
    if request.method == 'POST':
        form = BodegaForm(request.POST, request.FILES, instance=bodega)
        if form.is_valid():
            form.save()
            return redirect('detalle_bodega', pk=pk)
    else:
        form = BodegaForm(instance=bodega)
    return render(request, 'vinoteca/editar_bodega.html', {'form': form, 'bodega': bodega})


@login_required
@permission_required('vinoteca.delete_bodega', raise_exception=True)
def eliminar_bodega(request, pk):
    bodega = get_object_or_404(Bodega, pk=pk)
    if request.method == 'POST':
        bodega.delete()
        return redirect('lista_bodegas')
    return render(request, 'vinoteca/eliminar_bodega.html', {'bodega': bodega})


@login_required
def crear_compra(request):
    if request.method == 'POST':
        # Crear una nueva compra para el usuario actual
        compra = Compra.objects.create(usuario=request.user, estado='pendiente')
        
        # Procesar solo un item de la compra (solo una vino)
        vino_id = request.POST.get('vino_id')
        cantidad = request.POST.get('cantidad')
        
        if vino_id and cantidad:
            try:
                cantidad = int(cantidad)
                if cantidad > 0:
                    vino = get_object_or_404(Vino, pk=vino_id)
                    
                    # Verificar si hay suficiente stock
                    if vino.stock >= cantidad:
                        # Crear el item de compra
                        ItemCompra.objects.create(
                            compra=compra,
                            vino=vino,
                            cantidad=cantidad,
                            precio_unitario=vino.precio
                        )
                        
                        # Reducir el stock del vino
                        vino.stock -= cantidad
                        vino.save()
                    else:
                        messages.error(request, f'No hay suficiente stock para {vino.nombre}. Stock disponible: {vino.stock}')
            except ValueError:
                messages.error(request, 'Cantidad inválida')
        
        # Si todo salió bien, redirigir a la página de compras del usuario
        return redirect('mis_compras')
    
    # Obtener todos los vinos disponibles
    vinos = Vino.objects.filter(stock__gt=0).select_related('bodega', 'varietal', 'categoria')
    
    return render(request, 'vinoteca/crear_compra.html', {'vinos': vinos})

@login_required
def mis_compras(request):
    # Obtener las compras del usuario actual
    compras = Compra.objects.filter(usuario=request.user).order_by('-fecha')
    
    # Calcular el total para cada compra y cada item
    for compra in compras:
        compra.total = 0
        for item in compra.items.all():
            item.total = item.cantidad * item.precio_unitario
            compra.total += item.total
    
    return render(request, 'vinoteca/mis_compras.html', {'compras': compras})

@login_required
@permission_required('vinoteca.add_varietal', raise_exception=True)
def crear_varietal(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion', '')
        
        if nombre:
            Varietal.objects.create(nombre=nombre, descripcion=descripcion)
            messages.success(request, f'Varietal {nombre} creado exitosamente')
            return redirect('home')
        else:
            messages.error(request, 'El nombre es requerido')
    
    return render(request, 'vinoteca/crear_varietal.html')

@login_required
@permission_required('vinoteca.add_categoria', raise_exception=True)
def crear_categoria(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        
        if nombre:
            Categoria.objects.create(nombre=nombre)
            messages.success(request, f'Categoria {nombre} creada exitosamente')
            return redirect('home')
        else:
            messages.error(request, 'El nombre es requerido')
    
    return render(request, 'vinoteca/crear_categoria.html')
