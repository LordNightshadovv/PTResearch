# LaTeX equations in CYPT PowerPoints

Use this when a source deck has mathematical display equations whose typesetting matters. It records the method used for the Air Vortex theory slides 9–11. The equations visible in the current CYPT P10 Air Vortex deck are transparent image assets, not editable LaTeX or proven editable Office Math.

## Reliable display path

1. Keep each equation's LaTeX source in a versioned manifest, with its intended slide, size, color, and source citation. Review the notation, units, and scientific meaning before rendering. Preserve the source deck's equation order and surrounding explanation.
2. Parse the LaTeX with MathJax TeX input (`base` and `ams`) and render to SVG with `fontCache: 'none'`. Fail if MathJax emits an error node. Set an explicit color and SVG dimensions from its `viewBox`; retain the SVG as a vector source.
3. Rasterize that SVG to a transparent RGBA PNG at the size needed for the slide. The Air Vortex assets were 140 pixels high and displayed at about 0.62 inches high, roughly 225 pixels per inch; increase output resolution for larger equations. Keep the alpha channel and aspect ratio. Do not use a screenshot or opaque background.
4. Place the PNG as a separate, replaceable PowerPoint image. Put its LaTeX source and citation in the slide notes or a paired manifest. In WPS and Google Slides, the image can be moved or resized, but changing the mathematical content means editing the LaTeX source and regenerating the asset.
5. Render the finished deck in the intended application and inspect all equation images for legibility, clipping, color, transparency, and placement. Check the PNG dimensions and alpha channel before export. The Air Vortex build used `mathjax-full` for TeX-to-SVG and `sharp` for SVG-to-PNG; its historical example is `deliverables/p10-air-vortex-theory-ppt/build/make-equation-assets.mjs` in the PTResearch workspace. Treat that file as an example tied to its project inputs, not a ready-to-run general converter.

## Optional native PowerPoint equation layer

For an application that supports editable Office Math, the Air Vortex experiment converted LaTeX to MathML with `latex2mathml`, then MathML to OMML with `xsltproc` and an XSLT map. It placed OMML in an `a14:m` PowerPoint math choice and the transparent PNG in an `mc:Fallback` picture. It also saved the LaTeX source in notes. The project-specific example is `deliverables/p10-air-vortex-theory-ppt/build/embed-native-equations.py`.

That PPTX contains 11 OMML choices and 11 PNG fallbacks, but native equation editing was **not** verified in WPS or Microsoft PowerPoint. Package structure and a LibreOffice render establish neither which branch WPS displays nor whether edits survive saving. Before promising native editability, open the exported deck in the target app, edit a representative equation, save, reopen, and inspect the result. Google Slides may import only an image representation; test it separately when needed.

The earlier Air Vortex source contained malformed OMML that the bundled Artifact Tool could not parse, so that project used targeted OOXML/JSZip edits to preserve the rest of its 39-slide deck. Treat direct XML editing as a repair for that source, not as the default deck-authoring method. Validate ZIP/XML structure, slide rendering, and the list of changed package parts whenever using it.

This equation path is independent of the excluded third-party LaTeX Posters skill.
