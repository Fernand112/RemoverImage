# Importar las bibliotecas necesarias
from flask import Flask, request, send_file  # Para crear la aplicación Flask y manejar solicitudes
from flask_cors import CORS  # Para permitir solicitudes desde el frontend
from rembg import remove  # Para remover el fondo de las imágenes
from PIL import Image  # Para manipular imágenes
import io  # Para manejar datos en memoria
import base64  # Para codificar imágenes en base64 para SVG

# Crear la aplicación Flask
app = Flask(__name__)

# Habilitar CORS para permitir solicitudes desde el frontend
CORS(app)

# Función auxiliar para convertir color hexadecimal a tupla RGBA
def hex_to_rgba(hex_color):
    """
    Convierte un color hexadecimal (ej. #FFFFFF) a una tupla RGBA.
    Agrega alpha 255 para opacidad completa.
    """
    hex_color = hex_color.lstrip('#')  # Remover el símbolo #
    # Convertir cada par de caracteres a entero y crear tupla
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4)) + (255,)

# Endpoint para remover el fondo de la imagen
@app.route('/remove-background', methods=['POST'])
def remove_background():
    """
    Endpoint que recibe una imagen, remueve el fondo usando rembg,
    aplica un color de fondo personalizado y devuelve la imagen procesada.
    """
    # Verificar si se envió un archivo de imagen
    if 'image' not in request.files:
        return 'No se envió ningún archivo de imagen', 400

    # Obtener el archivo de imagen, el color de fondo y el formato
    file = request.files['image']
    bg_color = request.form.get('bg_color', '#FFFFFF')  # Color por defecto blanco
    output_format = request.form.get('format', 'png')  # Formato por defecto PNG

    # Abrir la imagen con PIL
    input_image = Image.open(file.stream)

    # Remover el fondo usando rembg
    output_image = remove(input_image)

    # Asegurarse de que la imagen esté en modo RGBA
    if output_image.mode != 'RGBA':
        output_image = output_image.convert('RGBA')

    # Crear una nueva imagen con el color de fondo deseado
    bg_rgba = hex_to_rgba(bg_color)
    background = Image.new('RGBA', output_image.size, bg_rgba)

    # Combinar la imagen sin fondo con el fondo coloreado
    final_image = Image.alpha_composite(background, output_image)

    # Preparar la respuesta según el formato solicitado
    if output_format.lower() == 'svg':
        # Guardar la imagen como PNG en memoria para incrustar en SVG
        img_io = io.BytesIO()
        final_image.save(img_io, 'PNG')
        img_io.seek(0)
        img_base64 = base64.b64encode(img_io.getvalue()).decode('utf-8')

        # Crear contenido SVG con la imagen incrustada
        svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{final_image.width}" height="{final_image.height}" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
    <image width="{final_image.width}" height="{final_image.height}" xlink:href="data:image/png;base64,{img_base64}"/>
</svg>'''

        # Devolver el SVG como respuesta
        svg_io = io.BytesIO(svg_content.encode('utf-8'))
        svg_io.seek(0)
        return send_file(svg_io, mimetype='image/svg+xml')

    elif output_format.lower() == 'jpg':
        # Guardar como JPG
        img_io = io.BytesIO()
        # Convertir a RGB si es RGBA para JPG
        if final_image.mode == 'RGBA':
            final_image = final_image.convert('RGB')
        final_image.save(img_io, 'JPEG', quality=95)
        img_io.seek(0)
        return send_file(img_io, mimetype='image/jpeg')

    else:  # PNG por defecto
        # Guardar como PNG
        img_io = io.BytesIO()
        final_image.save(img_io, 'PNG')
        img_io.seek(0)
        return send_file(img_io, mimetype='image/png')

# Ejecutar la aplicación si se ejecuta directamente
if __name__ == '__main__':
    # Ejecutar en todas las interfaces, puerto 3000, con modo debug
    app.run(host='0.0.0.0', port=3000, debug=True)