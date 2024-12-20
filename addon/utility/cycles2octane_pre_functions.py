import bpy

from .node_functions import create_node, create_node_link

# Functions that will run before the replaced node were created

# THESE FUNCTIONS SHOULD ALWAYS RETURN THE NODE


def OctaneUniversalMaterial(old_node):

    # Change bump input to normal input before converting

    bump_link = old_node.inputs["Bump"].links
    node_tree = old_node.id_data

    if bump_link:
        for link_b in bump_link:

            if not old_node.inputs["Normal"].links:

                link = node_tree.links.new
                link(link_b.from_socket, old_node.inputs["Bump"])
                node_tree.links.remove(link_b)

    return old_node


def ShaderNodeMapping(old_node):

    return old_node

    # Não sei pq fiz isso em baixo

    node_tree = old_node.id_data

    if old_node.inputs[0].links:

        add_node = node_tree.nodes.new("ShaderNodeVectorMath")
        add_node.operation = "ADD"
        add_node.location = old_node.location

        link = node_tree.links.new

        link(add_node.inputs[0], old_node.inputs[0].links[0].from_socket)

        if old_node.inputs["Location"].links:
            link(add_node.inputs[1], old_node.inputs[1].links[0].from_socket)

        link(add_node.outputs[0], old_node.inputs[1])

    return old_node




def ShaderNodeTexImage(old_node):
    """Pre-conversion function dla noda tekstury"""
    
    # Zapisz informacje o obrazie do wykorzystania później
    if old_node.image:
        old_node["image_filepath"] = old_node.image.filepath
        old_node["image_name"] = old_node.image.name
    
    # Sprawdź czy tekstura jest podłączona do bump mapping
    if old_node.outputs["Color"].links:
        for link in old_node.outputs["Color"].links:
            if link.to_node.bl_idname == "ShaderNodeBump":
                if link.to_socket.name == "Height":
                    # Zapisz wartość Strength z noda Bump
                    bump_strength = link.to_node.inputs["Strength"].default_value
                    old_node["bump_type"] = "height"
                    old_node["bump_strength"] = bump_strength

    # Istniejący kod dla kanału alpha
    if old_node.outputs["Alpha"].links:
        octane_alpha = create_node(
            old_node.id_data, 
            "ShaderNodeOctAlphaImageTex",
            [old_node.location[0], old_node.location[1] - (300 if old_node.outputs["Color"].links else 0)])

        octane_alpha.image = old_node.image

        for link in old_node.outputs["Alpha"].links:
            create_node_link(octane_alpha.id_data, link.to_socket,
                             octane_alpha.outputs[0])
    
    return old_node


def OctaneColorCorrection(old_node):

    new_node.inputs["Brightness"].default_value 
    new_node.inputs["Contrast"].default_value 
    new_node.inputs["Hue"].default_value = new_node.inputs["Hue"].default_value
    new_node.inputs["Saturation"].default_value

    return old_node
    