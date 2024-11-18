I am not the creator of this addon, I only adapted it to work with Blender 4.0+. Here is the author and a link to the original version.

https://github.com/RodrigoGama1902/cycles2octane


List of improvements made by me:

Here's the list of nodes converted from Cycles to Octane:

ShaderNodeHueSaturation (converted to OctaneColorCorrection)
ShaderNodeBrightContrast (converted to OctaneColorCorrection)
ShaderNodeRGB (converted to OctaneRGBColor)
ShaderNodeBsdfPrincipled (converted to OctaneUniversalMaterial)
ShaderNodeMapping (converted to Octane3DTransformation)
ShaderNodeOutputMaterial (converted to ShaderNodeOutputMaterial)
ShaderNodeTexImage (converted to OctaneRGBImage)
ShaderNodeValToRGB (converted to OctaneGradientMap)
ShaderNodeMix (converted to OctaneCyclesMixColorNodeWrapper)
ShaderNodeBsdfTranslucent (converted to OctaneUniversalMaterial with OctaneRGB Color wich mimic translucent in Octane)
ShaderNodeInvert (converted to OctaneInvertTexture)
ShaderNodeBsdfTransparent (converted to OctaneNullMaterial)
ShaderNodeAddShader (converted to OctaneMixMaterial)
ShaderNodeMixShader (converted to OctaneMixMaterial)
ShaderNodeMapRange (converted to OctaneOperatorRange)
ShaderNodeMath (converted to OctaneCyclesNodeMathNodeWrapper)
ShaderNodeVectorMath (converted to OctaneCyclesNodeVectorMathNodeWrapper)
ShaderNodeTexNoise (converted to OctaneCinema4DNoise)
ShaderNodeGamma (converted to OctaneColorCorrection)
ShaderNodeBump (converted to null node group which mimic bump node)
ShaderNodeNormalMap (converted to null node group which mimic normal map node)
ShaderNodeDisplacement (converted to OctaneTextureDisplacement)
ShaderNodeEmission (converted to OctaneTextureEmission)
ShaderNodeBlackbody (converted to OctaneBlackBodyEmission)


All nodes are compatible with Blender 4.2. Earlier versions have several incompatibilities when it comes to sockets(such as Principled BSDF or Material Output)for this reason this converter will not work on older versions of Blender.With my corrections, any convertible node values should be correctly transferred during Octane conversion. I removed the reverse conversion, which after my corrections began to whirr and generate a mass of errors
