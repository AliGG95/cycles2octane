import bpy

from .node_functions import (
    replace_node,
    move_node_link_to_socket,
    convert_old_to_new_socket_value,
    create_node_link,
    create_node)
from mathutils import Vector
from math import degrees
from octane.utils import utility, consts

# Functions that will run after the replaced node were created

# PRINCIPLED NODES


def ShaderNodeBsdfPrincipled(new_node, old_node):

    return new_node


def ShaderNodeTexImage(new_node, old_node):

    new_node.image = old_node.image

    if old_node.bl_idname == "ShaderNodeOctAlphaImageTex":
        move_node_link_to_socket(new_node.outputs[0], 1)

    return new_node


import bpy
from mathutils import Vector
from math import degrees
from octane.utils import utility, consts





def ShaderNodeNormalMap(new_node, old_node):

    normal_output = new_node.outputs["Normal"]
    normal_link = normal_output.links

    if normal_link:
        for i in normal_link:
            to_node = i.to_node
            if to_node.bl_idname == "ShaderNodeBsdfPrincipled":

                node_tree = to_node.id_data

                node_tree.links.remove(i)

                link = node_tree.links.new

                link(normal_output, to_node.inputs["Normal"])

    return new_node


def OctaneCyclesMixColorNodeWrapper(new_node, old_node):
    """Post-conversion function for Mix node"""
    
    # Set blend type
    try:
        blend_type_mapping = {
            'MIX': 'Mix',
            'DARKEN': 'Darken',
            'MULTIPLY': 'Multiply', 
            'BURN': 'Burn',
            'LIGHTEN': 'Lighten',
            'SCREEN': 'Screen',
            'DODGE': 'Dodge',
            'ADD': 'Add',
            'OVERLAY': 'Overlay',
            'SOFT_LIGHT': 'Soft Light',
            'LINEAR_LIGHT': 'Linear Light',
            'DIFFERENCE': 'Difference',
            'EXCLUSION': 'Exclusion',
            'SUBTRACT': 'Subtract',
            'DIVIDE': 'Divide',
            'HUE': 'Hue',
            'SATURATION': 'Saturation',
            'COLOR': 'Color',
            'VALUE': 'Value'
        }
        if hasattr(old_node, "blend_type"):
            new_node.inputs[0].default_value = blend_type_mapping.get(old_node.blend_type, 'Mix')
    except Exception as e:
        print(f"Error setting blend type: {e}")

    try:
        # Clamp settings based on JSON socket indices
        clamp_factor = old_node.clamp_factor if hasattr(old_node, 'clamp_factor') else True
        clamp_result = old_node.clamp_result if hasattr(old_node, 'clamp_result') else False
        new_node.inputs["Clamp Factor"].default_value = int(clamp_factor)  # index 1
        new_node.inputs["Clamp Result"].default_value = int(clamp_result)  # index 2

        # Factor (Fac)
        fac_socket = old_node.inputs.get('Fac') or old_node.inputs.get('Factor')
        if fac_socket:
            if fac_socket.is_linked:
                for link in fac_socket.links:
                    new_node.id_data.links.new(link.from_socket, new_node.inputs["Factor"])  # index 5
            else:
                new_node.inputs["Factor"].default_value = fac_socket.default_value

        # Color1/A
        color1_socket = old_node.inputs.get('Color1') or old_node.inputs.get('A')
        if color1_socket:
            if color1_socket.is_linked:
                for link in color1_socket.links:
                    new_node.id_data.links.new(link.from_socket, new_node.inputs["A"])  # index 6
            elif hasattr(color1_socket, 'default_value'):
                new_node.inputs["A"].default_value = tuple(color1_socket.default_value[:3])

        # Color2/B
        color2_socket = old_node.inputs.get('Color2') or old_node.inputs.get('B')
        if color2_socket:
            if color2_socket.is_linked:
                for link in color2_socket.links:
                    new_node.id_data.links.new(link.from_socket, new_node.inputs["B"])  # index 7
            elif hasattr(color2_socket, 'default_value'):
                new_node.inputs["B"].default_value = tuple(color2_socket.default_value[:3])
        
    except Exception as e:
        print(f"Error setting values: {e}")
    
    return new_node

def ShaderNodeRGB(new_node, old_node):

    rgb = list(old_node.a_value)
    rgba = [i for i in rgb]
    rgba.append(1)

    new_node.outputs[0].default_value = rgba

    return new_node


def ShaderNodeMapRange(new_node, old_node):

    if old_node.inputs[1].default_value == "Linear":
        new_node.interpolation_type = 'LINEAR'

    if old_node.inputs[1].default_value == "Steps":
        new_node.interpolation_type = 'STEPPED'

    if old_node.inputs[1].default_value == "Smoothstep":
        new_node.interpolation_type = 'SMOOTHSTEP'

    if old_node.inputs[1].default_value == "Smootherstep":
        new_node.interpolation_type = "SMOOTHERSTEP"

    new_node.clamp = old_node.inputs['Clamp'].default_value

    return new_node

# OCTANE NODES


def OctaneUniversalMaterial(new_node, old_node):
    """Post-conversion function for Universal Material"""
    # Turn albedo black when detect transmission change
    if new_node.inputs['Transmission'].links:
        new_node.inputs['Albedo'].default_value = (0, 0, 0)

    if old_node.inputs.get('Transmission Weight'):
        if not old_node.inputs['Transmission Weight'].links:
            if not old_node.inputs['Transmission Weight'].default_value == 0:
                rgb_node = create_node(
                    new_node.id_data, "OctaneRGBColor", location=[new_node.location[0] - 200, new_node.location[1]])

                rgb_node.a_value = old_node.inputs["Base Color"].default_value[:-1]

                create_node_link(
                    rgb_node.id_data, rgb_node.outputs[0], new_node.inputs["Transmission"])

                new_node.inputs['Albedo'].default_value = (0, 0, 0)
                
    # Handle emission texture
    if old_node.inputs['Emission Color'].is_linked:
        original_texture = old_node.inputs['Emission Color'].links[0].from_node
        emission_node = None

        # Sprawdzamy czy to node BlackBody
        if original_texture.bl_idname == "ShaderNodeBlackbody":
            # Dla Blackbody szukamy już przekonwertowanego node'a
            for node in new_node.id_data.nodes:
                if node.bl_idname == "OctaneBlackBodyEmission":
                    if any(link.from_node == original_texture for link in node.inputs["Texture"].links):
                        emission_node = node
                        break
        # Jeśli to tekstura
        elif original_texture.bl_idname == "ShaderNodeTexImage":
            # Tworzymy TextureEmission
            emission_node = create_node(
                new_node.id_data, 
                "OctaneTextureEmission",
                location=[new_node.location[0] - 200, new_node.location[1] - 100]
            )
            
            # Szukamy przekonwertowanej tekstury
            original_image = original_texture.image
            for node in new_node.id_data.nodes:
                if (node.bl_idname == "OctaneRGBImage" and 
                    hasattr(node, 'image') and 
                    node.image == original_image):
                    # Łączymy znalezioną teksturę z TextureEmission
                    create_node_link(
                        new_node.id_data,
                        node.outputs[0],
                        emission_node.inputs["Texture"]
                    )
                    print(f"Connected texture {node.name} to TextureEmission")
                    break
                        
        # Podłączamy emission node do Universal Material
        if emission_node:
            create_node_link(
                new_node.id_data,
                emission_node.outputs["Emission out"], 
                new_node.inputs["Emission"]
            )

            # Set emission strength if available
            if not old_node.inputs['Emission Strength'].is_linked:
                emission_node.inputs["Power"].default_value = old_node.inputs['Emission Strength'].default_value

    return new_node
    
    
    
def OctaneCyclesNodeMathNodeWrapper(new_node, old_node):
    """Post-conversion function for Math node"""
    # Set operation
    if hasattr(old_node, "operation"):
        operation_mapping = {
            'ADD': 'Add', 'SUBTRACT': 'Subtract', 'MULTIPLY': 'Multiply', 'DIVIDE': 'Divide',
            'MULTIPLY_ADD': 'Multiply Add', 'POWER': 'Power', 'LOGARITHM': 'Logarithm',
            'SQRT': 'Square Root', 'INV_SQRT': 'Inverse Square Root', 'ABSOLUTE': 'Absolute',
            'MINIMUM': 'Minimum', 'MAXIMUM': 'Maximum', 'LESS_THAN': 'Less Than',
            'GREATER_THAN': 'Greater Than', 'SIGN': 'Sign', 'COMPARE': 'Compare',
            'SMOOTH_MIN': 'Smooth min', 'SMOOTH_MAX': 'Smooth max', 'ROUND': 'Round',
            'FLOOR': 'Floor', 'CEIL': 'Ceil', 'TRUNC': 'Truncate', 'FRACT': 'Fraction',
            'MODULO': 'Truncated Modulo', 'FLOORED_MODULO': 'Floored Modulo',
            'WRAP': 'Wrap', 'SNAP': 'Snap', 'PINGPONG': 'Pingpong', 'SINE': 'Sine',
            'COSINE': 'Cosine', 'TANGENT': 'Tangent', 'ARCSINE': 'Arcsine',
            'ARCCOSINE': 'Arccosine', 'ARCTANGENT': 'Arctangent', 'ARCTAN2': 'Arctan2',
            'SINH': 'Hyperbolic Sine', 'COSH': 'Hyperbolic Cosine',
            'TANH': 'Hyperbolic Tangent', 'RADIANS': 'Radians', 'DEGREES': 'Degrees'
        }
        new_node.inputs["Type"].default_value = operation_mapping.get(old_node.operation, 'Add')

    # Set clamp - directly setting the bool socket
    new_node.inputs["Clamp"].default_value = bool(old_node.use_clamp)

    # Copy values and connections for Value1, Value2, Value3
    input_names = ["Value1", "Value2", "Value3"]
    for i, name in enumerate(input_names):
        if i < len(old_node.inputs):
            old_socket = old_node.inputs[i]
            new_socket = new_node.inputs[name]

            # Copy value if not linked
            if not old_socket.is_linked:
                if isinstance(new_socket.default_value, float):
                    new_socket.default_value = float(old_socket.default_value)

            # Copy connection if linked
            if old_socket.is_linked:
                link = old_socket.links[0]
                new_node.id_data.links.new(link.from_socket, new_socket)

    # Update socket names based on operation
    operation_specific_names = {
        'WRAP': ['Value', 'Max', 'Min'],
        'MULTIPLY_ADD': ['Value', 'Multiplier', 'Addend'],
        'COMPARE': ['Value1', 'Value2', 'Epsilon'],
        'SMOOTH_MIN': ['Value1', 'Value2', 'Distance'],
        'SMOOTH_MAX': ['Value1', 'Value2', 'Distance'],
        'POWER': ['Base', 'Exponent', 'Value3']
    }

    if old_node.operation in operation_specific_names:
        names = operation_specific_names[old_node.operation]
        for i, name in enumerate(names):
            if i < len(input_names):
                new_node.inputs[input_names[i]].name = name

    return new_node
    
    
def OctaneCyclesNodeVectorMathNodeWrapper(new_node, old_node):
    """Post-conversion function for Vector Math node"""
    
    socket_indices = {
        "Type": 0,
        "Vector1": 1,
        "Vector2": 2, 
        "Vector3": 3,
        "Scale": 4
    }

    operation_mapping = {
        'ADD': 'Add',
        'SUBTRACT': 'Subtract', 
        'MULTIPLY': 'Multiply',
        'DIVIDE': 'Divide',
        'MULTIPLY_ADD': 'Multiply Add',
        'CROSS_PRODUCT': 'Cross Product',
        'PROJECT': 'Project', 
        'REFLECT': 'Reflect',
        'REFRACT': 'Refract',
        'FACEFORWARD': 'Faceforward',
        'DOT_PRODUCT': 'Dot Product',
        'DISTANCE': 'Distance',
        'LENGTH': 'Length',
        'SCALE': 'Scale',
        'NORMALIZE': 'Normalize',
        'ABSOLUTE': 'Absolute',
        'MINIMUM': 'Minimum',
        'MAXIMUM': 'Maximum',
        'FLOOR': 'Floor',
        'CEIL': 'Ceil',
        'FRACTION': 'Fraction',
        'MODULO': 'Modulo',
        'WRAP': 'Wrap',
        'SNAP': 'Snap',
        'SINE': 'Sine',
        'COSINE': 'Cosine',
        'TANGENT': 'Tangent'
    }

    # Handle Vector1
    if old_node.inputs[0].is_linked:
        new_node.id_data.links.new(
            old_node.inputs[0].links[0].from_socket,
            new_node.inputs[socket_indices["Vector1"]]
        )
    else:
        new_node.inputs[socket_indices["Vector1"]].default_value = old_node.inputs[0].default_value

    # Handle Vector2 if needed for operations requiring it
    vector2_ops = {'ADD', 'SUBTRACT', 'MULTIPLY', 'DIVIDE', 'CROSS_PRODUCT', 
                  'PROJECT', 'REFLECT', 'DOT_PRODUCT', 'DISTANCE', 'MINIMUM', 
                  'MAXIMUM', 'MODULO', 'SNAP'}
                  
    if hasattr(old_node, "operation") and old_node.operation in vector2_ops:
        if len(old_node.inputs) > 1 and old_node.inputs[1].is_linked:
            new_node.id_data.links.new(
                old_node.inputs[1].links[0].from_socket,
                new_node.inputs[socket_indices["Vector2"]]
            )
        elif len(old_node.inputs) > 1:
            new_node.inputs[socket_indices["Vector2"]].default_value = old_node.inputs[1].default_value

    # Handle Vector3 for special operations
    vector3_ops = {'MULTIPLY_ADD', 'FACEFORWARD', 'WRAP'}
    if hasattr(old_node, "operation") and old_node.operation in vector3_ops:
        if len(old_node.inputs) > 2 and old_node.inputs[2].is_linked:
            new_node.id_data.links.new(
                old_node.inputs[2].links[0].from_socket,
                new_node.inputs[socket_indices["Vector3"]]
            )
        elif len(old_node.inputs) > 2:
            new_node.inputs[socket_indices["Vector3"]].default_value = old_node.inputs[2].default_value

    # Handle Scale for specific operations
    if hasattr(old_node, "operation"):
        if old_node.operation == 'REFRACT':
            if len(old_node.inputs) > 2:
                if isinstance(old_node.inputs[2].default_value, (float, int)):
                    new_node.inputs[socket_indices["Scale"]].default_value = float(old_node.inputs[2].default_value)
                elif hasattr(old_node.inputs[2].default_value, '__len__'):
                    # If it's a vector/array, use first component
                    new_node.inputs[socket_indices["Scale"]].default_value = float(old_node.inputs[2].default_value[0])
        elif old_node.operation == 'SCALE':
            if len(old_node.inputs) > 1:
                if isinstance(old_node.inputs[1].default_value, (float, int)):
                    new_node.inputs[socket_indices["Scale"]].default_value = float(old_node.inputs[1].default_value)
                elif hasattr(old_node.inputs[1].default_value, '__len__'):
                    # If it's a vector/array, use first component
                    new_node.inputs[socket_indices["Scale"]].default_value = float(old_node.inputs[1].default_value[0])

    # Set operation type
    if hasattr(old_node, "operation") and old_node.operation in operation_mapping:
        new_node.inputs[socket_indices["Type"]].default_value = operation_mapping[old_node.operation]

    # Update socket visibility based on operation type
    vector_math_type = new_node.inputs[socket_indices["Type"]].default_value
    input_value1 = new_node.inputs[socket_indices["Vector1"]]
    input_value2 = new_node.inputs[socket_indices["Vector2"]]
    input_value3 = new_node.inputs[socket_indices["Vector3"]]
    input_scale = new_node.inputs[socket_indices["Scale"]]

    # Set visibility and names based on operation
    if vector_math_type in ("Length", "Normalize", "Absolute", "Floor", "Ceil", "Fraction", 
                           "Sine", "Cosine", "Tangent"):
        input_value1.hide = False
        input_value2.hide = True
        input_value3.hide = True
        input_scale.hide = True
        
    elif vector_math_type == "Scale":
        input_value1.hide = False
        input_value2.hide = True
        input_value3.hide = True
        input_scale.hide = False
        
    elif vector_math_type == "Refract":
        input_value1.hide = False
        input_value2.hide = False
        input_value3.hide = True
        input_scale.hide = False
        
    elif vector_math_type in ("Multiply Add", "Faceforward", "Wrap"):
        input_value1.hide = False
        input_value2.hide = False
        input_value3.hide = False
        input_scale.hide = True

    return new_node
    
    
    
def OctaneCinema4DNoise(new_node, old_node):
    """Post-conversion function for noise nodes"""
    
    noise_type_mapping = {
        'PERLIN': 'Noise',
        'VORONOI': 'Voronoi 1',
        'MULTIFRACTAL': 'FBM',
        'RIDGED_MULTIFRACTAL': 'Ridged Multi Fractal', 
        'HYBRID_MULTIFRACTAL': 'Fire',
        'FBM': 'FBM',
        'HETERO_TERRAIN': 'Turbulence',
        'MUSGRAVE': 'Wavy Turbulence',
        'CELL_NOISE': 'Cell Noise'
    }
    
    if hasattr(old_node, 'noise_type'):
        new_node.inputs['Noise type'].default_value = noise_type_mapping.get(
            old_node.noise_type, 'FBM')

    # Map power/scale    
    if old_node.inputs.get('Scale'):
        new_node.inputs['Power'].default_value = old_node.inputs['Scale'].default_value
        
    # Map detail to octaves (limit to 15)
    if old_node.inputs.get('Detail'):
        new_node.inputs['Octaves'].default_value = min(
            old_node.inputs['Detail'].default_value, 15.0)
            
    # Convert lacunarity with 1.05 scale factor
    if old_node.inputs.get('Lacunarity'):
        cycles_lac = old_node.inputs['Lacunarity'].default_value
        new_node.inputs['Lacunarity'].default_value = max(0.1, min(cycles_lac * 1.05, 10.0))
            
    # Map roughness to gain
    if old_node.inputs.get('Roughness'):
        new_node.inputs['Gain'].default_value = old_node.inputs['Roughness'].default_value * 0.25
    
    # Handle 4D noise
    if old_node.inputs.get('W'):
        new_node.inputs['Use 4D noise'].default_value = True
        new_node.inputs['T'].default_value = old_node.inputs['W'].default_value
        
    # Handle distortion via transform
    if old_node.inputs.get('Distortion') and old_node.inputs['Distortion'].default_value != 0:
        distortion = old_node.inputs['Distortion'].default_value
        transform_node = create_node(
            new_node.id_data,
            "Octane3DTransformation",
            location=[new_node.location[0] - 200, new_node.location[1]]
        )
        
        transform_node.inputs['Scale'].default_value = [
            1.0 + distortion,
            1.0 + distortion,
            1.0 + distortion
        ]
        
        create_node_link(
            new_node.id_data,
            transform_node.outputs[0],
            new_node.inputs['UVW transform']
        )
    
    return new_node




def OctaneRGBImage(new_node, old_node):
    """Post-conversion function dla RGB Image"""
    if hasattr(old_node, 'image') and old_node.image:
        new_node.image = old_node.image
        try:
            if old_node.image.colorspace_settings.name == 'Non-Color':
                new_node.inputs['Legacy gamma'].default_value = 1.0
        except:
            pass
    return new_node


def OctaneRGBColor(new_node, old_node):

    new_node.a_value = old_node.outputs[0].default_value[:-1]

    return new_node


def OctaneNullMaterial(new_node, old_node):

    if old_node.bl_idname == "ShaderNodeBsdfTransparent":
        new_node.inputs['Opacity'].default_value = 0

    return new_node


def OctaneMixTexture(new_node, old_node):

    if old_node.blend_type == 'MIX':
        return new_node

    else:
        replacement_node = None

        if old_node.blend_type == 'MULTIPLY':
            replacement_node = replace_node(new_node, "OctaneMultiplyTexture", {
                "1": 0, "2": 1}, {"0": 0})

        if old_node.blend_type == 'ADD':
            replacement_node = replace_node(new_node, "OctaneAddTexture", {
                "1": 0, "2": 1}, {"0": 0})

        if old_node.blend_type == 'SUBTRACT':
            replacement_node = replace_node(new_node, "OctaneSubtractTexture", {
                "1": 0, "2": 1}, {"0": 0})

        new_node.id_data.nodes.remove(new_node)

        return replacement_node


def OctaneColorVertexAttribute(new_node, old_node):

    new_node.inputs[0].default_value = old_node.layer_name

    return new_node


    
def OctaneColorCorrection(new_node, old_node):
    # Brightness
    if "Bright" in old_node.inputs:
        new_node.inputs["Brightness"].default_value = old_node.inputs["Bright"].default_value + 100
        
    else:
        new_node.inputs["Brightness"].default_value = 100  # Ustal wartość domyślną, jeśli nie istnieje

    # Contrast
    if "Contrast" in old_node.inputs:
        new_node.inputs["Contrast"].default_value = old_node.inputs["Contrast"].default_value
    else:
        new_node.inputs["Contrast"].default_value = 0

    # Hue
    if "Hue" in old_node.inputs:
        new_node.inputs["Hue"].default_value = old_node.inputs["Hue"].default_value * 2 - 1
    else:
        new_node.inputs["Hue"].default_value = 0

    # Saturation
    if "Saturation" in old_node.inputs:
        new_node.inputs["Saturation"].default_value = old_node.inputs["Saturation"].default_value * 100
    else:
        new_node.inputs["Saturation"].default_value = 100

    return new_node
    
    
def OctaneTextureDisplacement(new_node, old_node):
    # Znajdź node OctaneUniversalMaterial w drzewie node'ów
    universal_material_node = None
    for node in new_node.id_data.nodes:
        if node.bl_idname == "OctaneUniversalMaterial":
            universal_material_node = node
            break

    if universal_material_node:
        # Połącz wyjście "Displacement out" z wejściem "Displacement" w OctaneUniversalMaterial
        new_node.id_data.links.new(
            new_node.outputs["Displacement out"],
            universal_material_node.inputs["Displacement"]
        )

    return new_node


def OctaneTextureEmission(new_node, old_node):
    """Post-conversion function for Emission node"""
    if "Strength" in old_node.inputs:
        # Convert from Cycles watts/m² to Octane power setting
        cycles_strength = old_node.inputs["Strength"].default_value 
        new_node.inputs["Power"].default_value = cycles_strength
        new_node.inputs["Surface brightness"].default_value = True  # Enable W/m² mode

    if "Color" in old_node.inputs and not old_node.inputs["Color"].is_linked:
        new_node.inputs["Texture"].default_value = old_node.inputs["Color"].default_value[:3]

    return new_node


def OctaneOperatorRange(new_node, old_node):
   """Post-conversion function for MapRange node"""
   interpolation_mapping = {
       'LINEAR': "Linear",
       'STEPPED': "Steps", 
       'SMOOTHSTEP': "Smoothstep",
       'SMOOTHERSTEP': "Smootherstep"
   }
   new_node.inputs["Interpolation"].default_value = interpolation_mapping.get(old_node.interpolation_type, "Linear")
   return new_node

# NULL NODES GROUP





 

def OctaneGradientMap(new_node, old_node):
    """Post-konwersja dla ShaderNodeValToRGB (Color Ramp) na OctaneGradientMap"""
    
    # Inicjalizacja pomocniczego node'a poprzez wbudowane funkcje Octane
    temp_node = utility.get_octane_helper_node(new_node.name)
    if temp_node is None:
        new_node.init_color_ramp_helper_node()
        new_node.loads_color_ramp_data()
        new_node.update_value_sockets()
        new_node.dumps_color_ramp_data()
    
    # Pobierz color ramp z helper node'a    
    new_color_ramp = utility.get_octane_helper_node(new_node.color_ramp_name).color_ramp
    
    # Kopiowanie elementów
    for i in range(len(old_node.color_ramp.elements)):
        if i <= len(new_color_ramp.elements) - 1:
            # Aktualizacja istniejących elementów
            new_color_ramp.elements[i].color = old_node.color_ramp.elements[i].color
            new_color_ramp.elements[i].position = old_node.color_ramp.elements[i].position
        else:
            # Dodawanie nowych elementów
            new_element = new_color_ramp.elements.new(old_node.color_ramp.elements[i].position)
            new_element.color = old_node.color_ramp.elements[i].color
        
    return new_node
    
def Octane3DTransformation(new_node, old_node):
    # Przenieś wartości Location i Rotation bez zmian
    new_node.inputs["Translation"].default_value = old_node.inputs["Location"].default_value
    new_node.inputs["Rotation"].default_value = old_node.inputs["Rotation"].default_value
    
    # Przelicz wartość Scale
    old_scale = old_node.inputs["Scale"].default_value
    new_scale = [1/old_scale[0] if old_scale[0] != 0 else 1,
                 1/old_scale[1] if old_scale[1] != 0 else 1,
                 1/old_scale[2] if old_scale[2] != 0 else 1]
    new_node.inputs["Scale"].default_value = new_scale

    return new_node