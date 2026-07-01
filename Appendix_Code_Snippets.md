# Thesis Appendix: Implementation Code Snippets

## Section A — CNN-only implementation

### File
- `c:\Users\mlenj\Music\Docugraph_CnnOnly\backend\cnn_only_model.py`

### Snippet 1: `CNNOnlyLayoutAnalyzer.analyze_layout_cnn_only`
- Lines `54-119`
- Purpose: CNN-only layout detection and prediction extraction using Detectron2.

```python
    def analyze_layout_cnn_only(self, image_array: np.ndarray) -> Dict[str, Any]:  # define the analysis method with typed arguments
        """ # perform this step
        CNN-only layout analysis without graph components # perform this step
        
        Args: # perform this step
            image_array: numpy array (H×W×C) # perform this step
        
        Returns: # perform this step
            Dict with CNN predictions, confidence scores, and feature maps # open a context block
        """ # perform this step
        if not self.initialized or self.model is None:  # if the model is not ready
            return self._fallback_analysis(image_array)  # use the fallback analyzer instead
        
        try: # try this block and catch errors
            # Convert to PIL Image
            if isinstance(image_array, np.ndarray):  # if input is a NumPy array
                image = Image.fromarray(image_array.astype('uint8'))  # convert array pixels to a PIL image
            else: # handle the alternate case
                image = image_array  # assume the input is already a PIL image
            
            # Run CNN detection (Detectron2)
            layout = self.model.detect(image)  # detect layout blocks in the image
            
            # Extract CNN predictions with normalized bboxes
            h, w = image_array.shape[:2]  # get original image height and width
            cnn_predictions = []  # prepare an empty list for predictions
            for block in layout:  # iterate over detected layout blocks
                norm_bbox = self._normalize_bbox(block.x_1, block.y_1, block.x_2, block.y_2, w, h)  # normalize coordinates to relative values
                bw = block.x_2 - block.x_1  # compute block width in pixels
                bh = block.y_2 - block.y_1  # compute block height in pixels
                pred = { # store this value
                    'type': block.type,  # block category such as Text, Title, Table
                    'bbox': norm_bbox,  # normalized bounding box values
                    'bbox_px': [block.x_1, block.y_1, block.x_2, block.y_2],  # raw pixel bounding box
                    'confidence': float(block.score) if hasattr(block, 'score') else 0.95,  # detection confidence score
                    'area': bw * bh,  # block area in pixels
                    'features': { # perform this step
                        'width': bw,  # block width in pixels
                        'height': bh,  # block height in pixels
                        'aspect_ratio': bw / bh if bh > 0 else 0  # width-to-height ratio
                    } # perform this step
                } # perform this step
                cnn_predictions.append(pred)  # save the prediction
            
            # Extract CNN feature maps
            feature_maps = self._extract_cnn_features(image_array, cnn_predictions)  # create a visual overlay for the predictions
            
            return { # return this value
                'success': True,  # mark the output as successful
                'model': 'CNN-only (Detectron2)',  # report which backend was used
                'predictions': cnn_predictions,  # list of detected layout blocks
                'prediction_count': len(cnn_predictions),  # number of blocks detected
                'feature_maps': feature_maps,  # visualization data for the front-end
                'statistics': { # perform this step
                    'total_blocks': len(cnn_predictions),  # total detected blocks
                    'avg_confidence': np.mean([p['confidence'] for p in cnn_predictions]) if cnn_predictions else 0,  # average confidence
                    'layout_accuracy': self._calculate_layout_accuracy(cnn_predictions),  # computed layout accuracy
                    'type_distribution': self._get_type_distribution(cnn_predictions),  # counts of each block type
                    'image_shape': list(image_array.shape)  # original image dimensions
                } # perform this step
            } # perform this step
        
        except Exception as e:  # handle unexpected errors
            print(f"CNN analysis error: {e}")  # log error for debugging
            return self._fallback_analysis(image_array)  # fallback to a simpler analysis
```

### Snippet 2: `CNNOnlyLayoutAnalyzer._extract_cnn_features`
- Lines `120-158`
- Purpose: create feature visualizations and encode CNN prediction outputs for API use.

```python
    def _extract_cnn_features(self, image_array: np.ndarray, predictions: List[Dict]) -> Dict:  # define feature extraction helper
        """Extract CNN-specific features from predictions""" # perform this step
        h, w = image_array.shape[:2]  # get image height and width
        
        # Create feature visualization
        feature_map = np.zeros((h, w, 3), dtype=np.uint8)  # blank RGB image for drawing
        
        # Color code by type
        type_colors = { # store this value
            'Text': (100, 100, 100),  # gray for text
            'Title': (255, 0, 0),  # red for titles
            'List': (0, 255, 0),  # green for lists
            'Table': (0, 0, 255),  # blue for tables
            'Figure': (255, 255, 0)  # yellow for figures
        } # perform this step
        
        for pred in predictions:  # loop over each predicted block
            x1, y1, x2, y2 = [int(v) for v in pred['bbox']]  # convert normalized bbox values to integers
            block_type = pred['type']  # get the detected block type
            color = type_colors.get(block_type, (128, 128, 128))  # use fallback color if unknown
            
            # Draw bounding box
            cv2.rectangle(feature_map, (x1, y1), (x2, y2), color, 2)  # outline the block area
            
            # Fill transparency
            overlay = feature_map.copy()  # duplicate current visualization
            cv2.rectangle(overlay, (x1, y1), (x2, y2), color, -1)  # fill the block area
            feature_map = cv2.addWeighted(feature_map, 0.7, overlay, 0.3, 0)  # blend the overlay with transparency
        
        # Convert to base64 for API
        import base64  # import here to keep dependencies local
        _, buffer = cv2.imencode('.png', feature_map)  # encode image as PNG bytes
        feature_map_b64 = base64.b64encode(buffer).decode()  # convert bytes to a text-friendly string
        
        return { # return this value
            'visualization': f'data:image/png;base64,{feature_map_b64}',  # inline image string
            'type_map': 'CNN feature detection visualization'  # descriptive label
        } # perform this step
```

### Snippet 3: `CNNOnlyLayoutAnalyzer._calculate_layout_accuracy`
- Lines `167-197`
- Purpose: compute composite layout accuracy from detection confidences and region counts.

```python
    def _calculate_layout_accuracy(self, predictions: List[Dict]) -> float:  # define method to score the layout quality
        """ # perform this step
        Calculate layout accuracy as a function of: # perform this step
        - Average confidence of detected regions # perform this step
        - Region count (more regions = better detection) # store this value
        - Confidence distribution variance # perform this step
        
        Returns: accuracy score 0-1 # perform this step
        """ # perform this step
        if not predictions:  # if there are no predictions
            return 0.0  # return zero accuracy
        
        # Get confidence scores
        confidences = [p.get('confidence', 0.5) for p in predictions]  # extract confidence values
        avg_conf = np.mean(confidences) if confidences else 0.5  # average confidence
        
        # Region count factor (logarithmic scale, capped)
        region_count = len(predictions)  # how many blocks were found
        region_factor = min(1.0, np.log(region_count + 1) / 4.0)  # more blocks improves score, but with diminishing returns
        
        # Confidence stability (lower variance = more stable)
        conf_std = np.std(confidences) if len(confidences) > 1 else 0.0  # standard deviation of confidences
        stability_factor = 1.0 - (conf_std * 0.3)  # reduce score when confidence is inconsistent
        stability_factor = max(0.5, stability_factor)  # keep a minimum stability score
        
        # Combine factors: average confidence + region detection boost + stability
        layout_accuracy = (avg_conf * 0.6 + region_factor * 0.25 + stability_factor * 0.15)  # weighted blend
        
        return float(min(1.0, max(0.0, layout_accuracy)))  # ensure the final score is between 0 and 1
```

### Snippet 4: `CNNOnlyLayoutAnalyzer._fallback_analysis`
- Lines `209-326`
- Purpose: fallback contour- and edge-based layout detection when LayoutParser is unavailable.

```python
    def _fallback_analysis(self, image_array: np.ndarray) -> Dict:  # define a backup layout analysis method
        """ # perform this step
        Fallback CNN analysis when LayoutParser not available # perform this step
        Uses grid-based layout detection and contour analysis # perform this step
        """ # perform this step
        h, w = image_array.shape[:2]  # read image height and width
        
        # Convert to grayscale for edge detection
        if len(image_array.shape) == 3:  # if image has color channels
            gray = cv2.cvtColor(image_array, cv2.COLOR_BGR2GRAY)  # convert to grayscale
        else: # handle the alternate case
            gray = image_array  # already grayscale
        
        # Detect edges
        edges = cv2.Canny(gray, 100, 200)  # find strong edges in the image
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)  # extract outer shapes
        
        predictions = []  # list to hold fallback predictions
        
        # Extract largest contours as blocks
        for contour in sorted(contours, key=cv2.contourArea, reverse=True)[:5]:  # top 5 largest shapes
            x, y, bw, bh = cv2.boundingRect(contour)  # bounding rectangle for the contour
            
            # Filter small contours
            if bw < 20 or bh < 20:  # ignore tiny noise regions
                continue # perform this step
            
            # Normalize bbox to percentages
            norm_bbox = self._normalize_bbox(x, y, x + bw, y + bh, w, h)  # convert pixel coords to relative values
            
            # Heuristic confidence scoring for fallback:
            # - area_ratio: contour area relative to image area (larger blocks -> higher confidence)
            # - solidity: contour area divided by bounding-box area (more filled -> higher confidence)
            # - edge_strength: average Canny response inside the bbox (stronger edges -> higher confidence)
            area = float(bw * bh)  # area of the bounding box
            area_ratio = area / float(w * h) if (w * h) > 0 else 0.0  # proportion of page covered
            bbox_area = float(bw * bh) if (bw * bh) > 0 else 1.0  # safe denominator for solidity
            contour_area = float(cv2.contourArea(contour))  # actual contour pixel area
            solidity = (contour_area / bbox_area) if bbox_area > 0 else 0.0  # fill ratio of the shape

            # Edge strength within bbox
            try: # try this block and catch errors
                roi = edges[y:y+bh, x:x+bw]  # region of interest inside the bounding box
                edge_strength = float(roi.mean() / 255.0) if roi.size > 0 else 0.0  # average edge intensity
            except Exception: # handle errors from the try block
                edge_strength = 0.0  # fallback when ROI extraction fails

            # Normalize area_ratio to a 0-1 scale (heuristic): multiply by 8 and clamp
            norm_area = min(1.0, area_ratio * 8.0)  # make small blocks count more

            # Weighted combination
            score = 0.5 * norm_area + 0.3 * solidity + 0.2 * edge_strength  # combine scoring features
            # Map to reasonable confidence range [0.4, 0.95]
            confidence = float(max(0.0, min(1.0, score)))  # clamp score to 0-1
            confidence = 0.4 + (confidence * 0.55)  # scale into a realistic confidence band

            predictions.append({ # add this item to the result list
                'type': 'Text',  # fallback assumes text-like blocks
                'bbox': norm_bbox,  # normalized bounding box
                'bbox_px': [x, y, x + bw, y + bh],  # pixel coordinates
                'confidence': confidence,  # estimated confidence score
                'area': bw * bh,  # area in pixels
                'features': { # perform this step
                    'width': bw,  # width in pixels
                    'height': bh,  # height in pixels
                    'aspect_ratio': bw / bh if bh > 0 else 0,  # shape ratio
                    'solidity': solidity,  # contour solidity
                    'edge_strength': edge_strength,  # edge density inside box
                    'area_ratio': area_ratio  # relative block area
                } # perform this step
            }) # perform this step
        
        # If no contours detected, use full page
        if not predictions:  # fallback to a single full-page block
            norm_bbox = self._normalize_bbox(0, 0, w, h, w, h)  # full-image normalized box
            # Heuristic for full-page confidence: based on overall edge density
            try: # try this block and catch errors
                edge_strength = float(edges.mean() / 255.0) if edges.size > 0 else 0.0  # average edge density for the whole image
            except Exception: # handle errors from the try block
                edge_strength = 0.0  # safe fallback
            # Map to range [0.45, 0.7]
            confidence = 0.45 + (edge_strength * 0.25)  # lower confidence for fallback
            predictions.append({ # add this item to the result list
                'type': 'Text',  # treat the whole page as a text block
                'bbox': norm_bbox, # perform this step
                'bbox_px': [0, 0, w, h], # perform this step
                'confidence': confidence, # perform this step
                'area': h * w, # perform this step
                'features': { # perform this step
                    'width': w, # perform this step
                    'height': h, # perform this step
                    'aspect_ratio': w / h if h > 0 else 0, # handle the alternate case
                    'edge_strength': edge_strength # perform this step
                } # perform this step
            }) # perform this step
        
        avg_confidence = np.mean([p['confidence'] for p in predictions]) if predictions else 0.5  # overall confidence average
        
        return { # return this value
            'success': True,  # fallback still returns success
            'model': 'CNN-only (Fallback - Edge Detection)',  # mark this as fallback mode
            'predictions': predictions,  # fallback predictions list
            'prediction_count': len(predictions),  # count of predicted blocks
            'feature_maps': {},  # no feature visualization for fallback
                'statistics': { # perform this step
                    'total_blocks': len(predictions),  # total blocks found
                    'avg_confidence': float(avg_confidence),  # average confidence
                    'layout_accuracy': self._calculate_layout_accuracy(predictions),  # fallback accuracy score
                    'type_distribution': {'Text': len(predictions)},  # only text blocks are returned
                    'image_shape': list(image_array.shape),  # original image shape
                    'fallback': True,  # mark that fallback logic was used
                    'fallback_confidence_method': 'area_ratio*0.5 + solidity*0.3 + edge_strength*0.2 (mapped to 0.4-0.95)' # perform this step
                } # perform this step
        } # perform this step
```

## Section C — File-to-Image Converter

### File
- `c:\Users\mlenj\Music\Docugraph_CnnOnly\filetoimageconverter.html`
- `C:\Users\mlenj\Music\DOCUGRAPH_WEBSITE\filetoimageconverter.html`

### Snippet 1: `convertAll`
- Lines `650-712`
- Purpose: orchestrates batch conversion of selected PDF, Word, and image pages.

```js
    async function convertAll() { // define an asynchronous function
      // Select only files with chosen pages and that have finished loading metadata.
      const convertible = files.filter(e => e.selectedPages.size > 0 && e.status !== 'loading'); // define a constant value
      if (!convertible.length) { // check condition
        showToast('Select at least one page to convert.'); // perform this step
        return; // return this value
      } // perform this step

      // Reset the UI and prepare for new conversion results.
      resultBlobs = []; // store this value
      document.getElementById('results-grid').innerHTML = ''; // store this value
      document.getElementById('success-banner').style.display = 'none'; // store this value
      document.getElementById('results').classList.remove('visible'); // perform this step

      // Read export options from the page controls.
      const scale = parseFloat(document.getElementById('opt-scale').value); // define a constant value
      const quality = parseFloat(document.getElementById('opt-quality').value); // define a constant value
      const bg = document.getElementById('opt-bg').value; // define a constant value
      document.getElementById('progress-wrap').style.display = ''; // store this value
      const btn = document.getElementById('btn-convert'); // define a constant value
      btn.disabled = true; // store this value
      btn.textContent = 'Converting…'; // store this value

      // Track progress across all selected pages.
      const totalPages = convertible.reduce((sum, entry) => sum + entry.selectedPages.size, 0); // define a constant value
      let donePages = 0; // define a variable

      for (const entry of convertible) { // repeat for each item
        setEntryStatus(entry, 'converting'); // perform this step
        updateBadge(entry); // perform this step
        try { // try this block and catch errors
          let blobs; // define a variable

          // Convert each file type with the dedicated helper.
          if (isPdf(entry.file)) { // check condition
            blobs = await convertPdf(entry, { scale, quality, bg }, () => { // wait for this operation to complete
              donePages += 1; // store this value
              setProgress((donePages / totalPages) * 100, `${donePages} / ${totalPages} pages…`); // perform this step
            }); // perform this step
          } else if (isDoc(entry.file)) { // perform this step
            blobs = await convertDoc(entry, { scale, quality, bg }); // store this value
            donePages += entry.selectedPages.size; // store this value
            setProgress((donePages / totalPages) * 100, `${donePages} / ${totalPages} pages…`); // perform this step
          } else { // perform this step
            blobs = await convertImage(entry.file, { scale, quality, bg }); // store this value
            donePages += 1; // store this value
            setProgress((donePages / totalPages) * 100, `${donePages} / ${totalPages} pages…`); // perform this step
          } // perform this step

          // Store converted images and update the display.
          blobs.forEach(b => resultBlobs.push(b)); // add this item to the result list
          appendResults(blobs); // perform this step
          setEntryStatus(entry, 'done'); // perform this step
        } catch (err) { // perform this step
          setEntryStatus(entry, 'error'); // perform this step
          showToast(`Error processing ${entry.file.name}: ${err.message || err}`); // perform this step
          console.error(err); // perform this step
        } // perform this step
        updateBadge(entry); // perform this step
      } // perform this step

      // Finalize UI state.
      setProgress(100, `${resultBlobs.length} image${resultBlobs.length !== 1 ? 's' : ''} ready`); // perform this step
      btn.disabled = false; // store this value
      btn.textContent = 'Convert selected pages →'; // store this value
      document.getElementById('results').classList.add('visible'); // perform this step
      document.getElementById('success-banner').style.display = ''; // store this value
      document.getElementById('success-msg').textContent = `✨ ${resultBlobs.length} image${resultBlobs.length !== 1 ? 's' : ''} ready to download!`; // perform this step
      document.getElementById('results-title').textContent = `Converted images (${resultBlobs.length})`; // store this value
      document.getElementById('results').scrollIntoView({ behavior: 'smooth', block: 'start' }); // perform this step
    } // perform this step
```

#### Line-by-line explanation
- `const convertible = files.filter(...)`: selects only queue entries with at least one page chosen and that are not still loading.
- `showToast(...)`: alerts the user when no valid page is selected.
- `resultBlobs = []`: clears previous conversion results.
- `document.getElementById('results-grid').innerHTML = ''`: clears any displayed output cards.
- `const scale = ...`: reads the export DPI/scale option from the UI.
- `const quality = ...`: reads the image compression quality option.
- `const bg = ...`: chooses the background color for output images.
- `btn.disabled = true`: disables the convert button while conversion runs.
- `totalPages = convertible.reduce(...)`: counts every selected page across all files.
- `for (const entry of convertible)`: loops through each file in the queue.
- `setEntryStatus(entry, 'converting')`: marks the item as converting for the UI.
- `if (isPdf(entry.file))`: routes PDF files to `convertPdf`.
- `else if (isDoc(entry.file))`: routes Word documents to `convertDoc`.
- `else`: handles images directly through `convertImage`.
- `blobs.forEach(b => resultBlobs.push(b))`: collects the generated blobs.
- `appendResults(blobs)`: renders thumbnail cards for each output image.
- `setProgress(...)`: updates the progress bar and label.
- `document.getElementById('results').scrollIntoView(...)`: scrolls the completed output into view.

### Snippet 2: `convertPdf`, `convertDoc`, `convertImage`
- Lines `712-842`
- Purpose: render PDF pages, Word document pages, and raster images to downloadable image blobs.

```js
    async function convertPdf(entry, { scale, quality, bg }, onPage) { // define an asynchronous function
      const pdf = entry.pdfDoc; // define a constant value
      const baseName = entry.file.name.replace(/\.pdf$/i, ''); // define a constant value
      const pages = [...entry.selectedPages].sort((a, b) => a - b); // define a constant value
      const blobs = []; // define a constant value
      for (const pageNum of pages) { // repeat for each item
        const page = await pdf.getPage(pageNum); // define a constant value
        const vp = page.getViewport({ scale }); // define a constant value
        const canvas = document.createElement('canvas'); // define a constant value
        canvas.width = vp.width; // store this value
        canvas.height = vp.height; // store this value
        const ctx = canvas.getContext('2d'); // define a constant value
        if (bg === 'white') { // check condition
          ctx.fillStyle = '#ffffff';
          ctx.fillRect(0, 0, canvas.width, canvas.height); // perform this step
        } // perform this step
        await page.render({ canvasContext: ctx, viewport: vp }).promise; // wait for this operation to complete
        const blob = await canvasToBlob(canvas, quality); // define a constant value
        blobs.push({ blob, name: `${baseName}_p${pageNum}.${outputFmt}` }); // add this item to the result list
        onPage(1); // perform this step
      } // perform this step
      return blobs; // return this value
    } // perform this step

    async function convertDoc(entry, { scale, quality, bg }) { // define an asynchronous function
      const baseName = entry.file.name.replace(/\.(doc|docx)$/i, ''); // define a constant value
      const html = entry.docContent ? entry.docContent : '<div>Could not extract document content.</div>'; // define a constant value
      const blobs = []; // define a constant value

      const measureContainer = document.createElement('div'); // define a constant value
      measureContainer.innerHTML = html; // store this value
      applyDocumentStyles(measureContainer); // perform this step
      measureContainer.style.position = 'absolute'; // store this value
      measureContainer.style.left = '-99999px'; // store this value
      measureContainer.style.top = '0'; // store this value
      measureContainer.style.width = '800px'; // store this value
      measureContainer.style.backgroundColor = '#ffffff';
      measureContainer.style.padding = '40px'; // store this value
      measureContainer.style.pointerEvents = 'none'; // store this value
      measureContainer.style.overflow = 'visible'; // store this value

      document.body.appendChild(measureContainer); // perform this step
      await new Promise(resolve => setTimeout(resolve, 200)); // wait for this operation to complete
      const totalHeight = measureContainer.scrollHeight; // define a constant value
      const pageHeight = 950; // define a constant value
      const numPages = Math.max(1, Math.ceil(totalHeight / pageHeight)); // define a constant value
      document.body.removeChild(measureContainer); // perform this step

      try { // try this block and catch errors
        for (let pageNum = 1; pageNum <= numPages; pageNum++) { // repeat for each item
          const wrapper = document.createElement('div'); // define a constant value
          wrapper.style.position = 'fixed'; // store this value
          wrapper.style.left = '0'; // store this value
          wrapper.style.top = '0'; // store this value
          wrapper.style.width = '800px'; // store this value
          wrapper.style.height = pageHeight + 'px'; // store this value
          wrapper.style.backgroundColor = '#ffffff';
          wrapper.style.overflow = 'hidden'; // store this value
          wrapper.style.zIndex = '-99999'; // store this value
          wrapper.style.pointerEvents = 'none'; // store this value

          const container = document.createElement('div'); // define a constant value
          container.innerHTML = html; // store this value
          applyDocumentStyles(container); // perform this step
          container.style.padding = '40px'; // store this value
          container.style.width = '100%'; // store this value
          container.style.boxSizing = 'border-box'; // store this value
          const offset = (pageNum - 1) * pageHeight; // define a constant value
          container.style.position = 'absolute'; // store this value
          container.style.top = (-offset) + 'px'; // store this value
          container.style.left = '0'; // store this value

          wrapper.appendChild(container); // perform this step
          document.body.appendChild(wrapper); // perform this step
          await new Promise(resolve => setTimeout(resolve, 200)); // wait for this operation to complete

          const canvas = await html2canvas(wrapper, { // define a constant value
            scale: 1, // perform this step
            backgroundColor: '#ffffff',
            logging: false, // perform this step
            useCORS: true, // perform this step
            allowTaint: true, // perform this step
            width: 800, // perform this step
            height: pageHeight, // perform this step
            windowHeight: pageHeight // perform this step
          }); // perform this step

          document.body.removeChild(wrapper); // perform this step

          const finalCanvas = document.createElement('canvas'); // define a constant value
          finalCanvas.width = Math.round(800 * scale); // store this value
          finalCanvas.height = Math.round(pageHeight * scale); // store this value
          const ctx = finalCanvas.getContext('2d'); // define a constant value
          ctx.scale(scale, scale); // perform this step
          ctx.drawImage(canvas, 0, 0); // perform this step

          const blob = await canvasToBlob(finalCanvas, quality); // define a constant value
          blobs.push({ blob, name: `${baseName}_p${pageNum}.${outputFmt}` }); // add this item to the result list
        } // perform this step

        return blobs; // return this value
      } catch (e) { // perform this step
        console.error('Doc conversion error:', e); // perform this step
        throw new Error(`Failed to convert document: ${e.message}`); // perform this step
      } // perform this step
    } // perform this step

    async function convertImage(file, { scale, quality, bg }) { // define an asynchronous function
      return new Promise((resolve, reject) => { // return this value
        const img = new Image(); // define a constant value
        const url = URL.createObjectURL(file); // define a constant value
        img.onload = async () => { // perform this step
          const canvas = document.createElement('canvas'); // define a constant value
          canvas.width = Math.round(img.naturalWidth * scale); // store this value
          canvas.height = Math.round(img.naturalHeight * scale); // store this value
          const ctx = canvas.getContext('2d'); // define a constant value
          if (bg === 'white') { // check condition
            ctx.fillStyle = '#ffffff';
            ctx.fillRect(0, 0, canvas.width, canvas.height); // perform this step
          } // perform this step
          ctx.drawImage(img, 0, 0, canvas.width, canvas.height); // perform this step
          URL.revokeObjectURL(url); // perform this step
          const blob = await canvasToBlob(canvas, quality); // define a constant value
          resolve([{ blob, name: file.name.replace(/\.[^.]+$/, '') + '.' + outputFmt }]); // perform this step
        }; // perform this step
        img.onerror = reject; // store this value
        img.src = url; // store this value
      }); // perform this step
    } // perform this step
```

#### Line-by-line explanation
- `const pdf = entry.pdfDoc;`: reuses the loaded PDF.js document object.
- `const baseName = ...`: derives a clean filename prefix.
- `const pages = [...entry.selectedPages].sort(...)`: converts the selected page set into an ordered array.
- `canvas.width = vp.width; canvas.height = vp.height;`: sets the render canvas to the exact PDF page dimensions.
- `if (bg === 'white') ...`: fills a white background so transparent PDF pages export cleanly.
- `await page.render(...).promise;`: rasterizes the PDF page using PDF.js.
- `const blob = await canvasToBlob(canvas, quality);`: converts the canvas into a binary image blob.
- `const measureContainer = document.createElement('div');`: builds a hidden document preview to measure how many pages the Word content will occupy.
- `container.style.left = '-99999px';`: keeps the measurement container off-screen.
- `const totalHeight = measureContainer.scrollHeight;`: reads the rendered document height.
- `const numPages = Math.max(1, Math.ceil(totalHeight / pageHeight));`: calculates page count based on a fixed page height.
- `wrapper.style.position = 'fixed'; ...`: positions each document page slice at the top-left corner for screenshot capture.
- `const canvas = await html2canvas(wrapper, { ... });`: renders the HTML page slice to a canvas using html2canvas.
- `ctx.scale(scale, scale);`: applies the selected output DPI/scale factor.
- `const blob = await canvasToBlob(finalCanvas, quality);`: saves each page as a final image blob.
- `const url = URL.createObjectURL(file);`: creates a temporary object URL for the image file.
- `img.onload = async () => { ... }`: waits for the image to load before drawing it to the canvas.
- `URL.revokeObjectURL(url);`: cleans up the temporary URL after use.

### Snippet 3: `loadPdfMeta`, `loadDocMeta`, `calculateDocPages`
- Lines `238-325`
- Purpose: load metadata for PDFs and Word files, estimate pages, and prepare the converter queue.

```js
    async function loadPdfMeta(entry) { // define an asynchronous function
      setEntryStatus(entry, 'loading'); // perform this step
      try { // try this block and catch errors
        const ab = await entry.file.arrayBuffer(); // define a constant value
        entry.pdfDoc = await pdfjsLib.getDocument({ data: ab }).promise; // store this value
        entry.numPages = entry.pdfDoc.numPages; // store this value
        for (let i = 1; i <= entry.numPages; i++) entry.selectedPages.add(i); // repeat for each item
        setEntryStatus(entry, 'ready'); // perform this step
        updateBadge(entry); // perform this step
        updateSelInfo(entry); // perform this step
        renderQueue(); // perform this step
        showPanels(); // perform this step
      } catch (e) { // perform this step
        setEntryStatus(entry, 'error'); // perform this step
      } // perform this step
    } // perform this step

    async function loadDocMeta(entry) { // define an asynchronous function
      setEntryStatus(entry, 'loading'); // perform this step
      try { // try this block and catch errors
        if (!window.mammoth) { // check condition
          throw new Error('Mammoth.js library not loaded'); // perform this step
        } // perform this step
        const ab = await entry.file.arrayBuffer(); // define a constant value
        const result = await mammoth.convertToHtml({ arrayBuffer: ab }); // define a constant value
        entry.docContent = result.value; // store this value

        const tempDiv = document.createElement('div'); // define a constant value
        tempDiv.innerHTML = entry.docContent; // store this value
        tempDiv.querySelectorAll('*').forEach(el => el.removeAttribute('style')); // perform this step
        entry.docContent = tempDiv.innerHTML; // store this value

        const numPages = await calculateDocPages(entry.docContent); // define a constant value
        entry.numPages = numPages; // store this value

        for (let i = 1; i <= numPages; i++) { // repeat for each item
          entry.selectedPages.add(i); // perform this step
        } // perform this step

        setEntryStatus(entry, 'ready'); // perform this step
        updateBadge(entry); // perform this step
        updateSelInfo(entry); // perform this step
        renderQueue(); // perform this step
        showPanels(); // perform this step
      } catch (e) { // perform this step
        console.error('Doc loading error:', e); // perform this step
        setEntryStatus(entry, 'error'); // perform this step
        updateBadge(entry); // perform this step
        renderQueue(); // perform this step
        showToast(`Failed to load ${entry.file.name}: ${e.message}`); // perform this step
      } // perform this step
    } // perform this step

    async function calculateDocPages(html) { // define an asynchronous function
      return new Promise((resolve) => { // return this value
        const container = document.createElement('div'); // define a constant value
        container.innerHTML = html; // store this value
        applyDocumentStyles(container); // perform this step
        container.style.position = 'absolute'; // store this value
        container.style.left = '-99999px'; // store this value
        container.style.top = '0'; // store this value
        container.style.width = '800px'; // store this value
        container.style.backgroundColor = '#ffffff';
        container.style.padding = '40px'; // store this value
        container.style.pointerEvents = 'none'; // store this value

        document.body.appendChild(container); // perform this step
        setTimeout(() => { // perform this step
          const height = container.scrollHeight; // define a constant value
          document.body.removeChild(container); // perform this step
          const pageHeight = 950; // define a constant value
          const numPages = Math.max(1, Math.ceil(height / pageHeight)); // define a constant value
          resolve(numPages); // perform this step
        }, 200); // perform this step
      }); // perform this step
    } // perform this step
```

#### Line-by-line explanation
- `const ab = await entry.file.arrayBuffer();`: loads the raw file bytes into memory.
- `entry.pdfDoc = await pdfjsLib.getDocument({ data: ab }).promise;`: initializes PDF.js with the PDF file.
- `entry.numPages = entry.pdfDoc.numPages;`: stores the total PDF page count.
- `entry.selectedPages.add(i)`: preselects all pages on load.
- `const result = await mammoth.convertToHtml({ arrayBuffer: ab });`: converts a Word document to HTML in the browser.
- `tempDiv.querySelectorAll('*').forEach(el => el.removeAttribute('style'));`: strips inline styles from Word HTML to avoid inconsistent rendering.
- `const numPages = await calculateDocPages(entry.docContent);`: estimates the number of image pages required.
- `document.body.appendChild(container);` / `document.body.removeChild(container);`: uses an off-screen DOM element for layout measurement.
- `const pageHeight = 950;`: defines the document page height used for pagination.
- `Math.ceil(height / pageHeight)`: converts total content height into page count.

### Snippet 4: `applyDocumentStyles`
- Lines `220-259`
- Purpose: normalize imported Word HTML for consistent page rendering.

```js
    function applyDocumentStyles(container) { // define a function
      container.style.cssText = 'font-family: "Calibri", "Segoe UI", Arial, sans-serif !important; font-size: 11pt !important; line-height: 1.0 !important; color: #000 !important; text-align: left !important; margin: 0 !important; padding: 0 !important;';
      container.querySelectorAll('*').forEach(el => { // perform this step
        el.style.cssText += 'margin: 0 !important; padding: 0 !important; line-height: 1.0 !important;'; // store this value
      }); // perform this step
      const paragraphs = container.querySelectorAll('p'); // define a constant value
      paragraphs.forEach(p => { // perform this step
        p.style.cssText = 'margin: 0 0 4pt 0 !important; padding: 0 !important; line-height: 1.0 !important; font-size: 11pt !important; font-family: "Calibri", "Segoe UI", Arial, sans-serif !important; text-align: left !important;'; // store this value
      }); // perform this step
      const headings = container.querySelectorAll('h1, h2, h3, h4, h5, h6'); // define a constant value
      headings.forEach(h => { // perform this step
        h.style.cssText = 'font-weight: 700 !important; margin: 4pt 0 !important; padding: 0 !important; line-height: 1.0 !important; font-size: 11pt !important; font-family: "Calibri", "Segoe UI", Arial, sans-serif !important;'; // store this value
      }); // perform this step
      const lists = container.querySelectorAll('ul, ol'); // define a constant value
      lists.forEach(list => { // perform this step
        list.style.cssText = 'margin: 0 0 4pt 20pt !important; padding: 0 !important; list-style-position: outside !important;'; // store this value
      }); // perform this step
      const listItems = container.querySelectorAll('li'); // define a constant value
      listItems.forEach(li => { // perform this step
        li.style.cssText = 'margin: 0 0 2pt 0 !important; padding: 0 !important; line-height: 1.0 !important; font-size: 11pt !important;'; // store this value
      }); // perform this step
      const tables = container.querySelectorAll('table'); // define a constant value
      tables.forEach(table => { // perform this step
        table.style.cssText = 'border-collapse: collapse !important; margin: 4pt 0 !important; width: 100% !important; padding: 0 !important;'; // store this value
        const cells = table.querySelectorAll('td, th'); // define a constant value
        cells.forEach(cell => { // perform this step
          cell.style.cssText = 'border: 1px solid #666 !important; padding: 3pt !important; vertical-align: top !important; line-height: 1.0 !important; font-size: 11pt !important; margin: 0 !important;';
        }); // perform this step
      }); // perform this step
      container.querySelectorAll('div, span, article, section').forEach(el => { // perform this step
        el.style.cssText = 'margin: 0 !important; padding: 0 !important; line-height: inherit !important;'; // store this value
      }); // perform this step
    } // perform this step
```

#### Line-by-line explanation
- `container.style.cssText = ...`: sets a base document style that mimics Word formatting.
- `querySelectorAll('*')`: removes any residual margins and paddings from imported HTML.
- `paragraphs.forEach(...)`: enforces paragraph spacing, font, and line-height.
- `headings.forEach(...)`: standardizes heading weights and spacing.
- `lists.forEach(...)`: ensures lists render with consistent indentation and bullets.
- `cells.forEach(...)`: forces table cells to use borders and compact spacing.
- `querySelectorAll('div, span, article, section')`: applies a final cleanup pass to remove stray spacing.

## Section B — DocuGraph implementation

### File
- `c:\Users\mlenj\Music\DOCUGRAPH_WEBSITE\backend\app.py`

### Snippet 1: `LayoutAnalyzer.analyze_layout`
- Lines `107-159`
- Purpose: DOCUGRAPH layout detection and block extraction using LayoutParser.

```python
    def analyze_layout(self, image_array): # define the function
        """ # perform this step
        Analyze document layout using LayoutParser # perform this step
        
        Args: # perform this step
            image_array: numpy array (H×W×C) # perform this step
        
        Returns: # perform this step
            dict with layout blocks, hierarchy, and confidence scores # open a context block
        """ # perform this step
        if not self.initialized or self.model is None: # check condition
            return self._fallback_layout_analysis(image_array) # return this value
        
        try: # try this block and catch errors
            # Convert to PIL Image for LayoutParser
            if isinstance(image_array, np.ndarray): # check condition
                image = Image.fromarray(image_array.astype('uint8')) # store this value
            else: # handle the alternate case
                image = image_array # store this value
            
            # Run detection
            layout = self.model.detect(image) # store this value
            
            # Extract blocks with hierarchy
            blocks = [] # store this value
            for block in layout: # repeat for each item in the list
                block_info = { # store this value
                    'type': block.type, # perform this step
                    'bbox': [block.x_1, block.y_1, block.x_2, block.y_2], # perform this step
                    'confidence': float(block.score) if hasattr(block, 'score') else 0.95, # handle the alternate case
                    'text': block.text if hasattr(block, 'text') else None, # handle the alternate case
                    'category': self._categorize_block(block.type) # perform this step
                } # perform this step
                blocks.append(block_info) # add this item to the result list
            
            # Build hierarchy (reading order)
            hierarchy = self._build_hierarchy(blocks, image_array.shape) # store this value
            
            return { # return this value
                'success': True, # perform this step
                'blocks': blocks, # perform this step
                'hierarchy': hierarchy, # perform this step
                'page_info': { # perform this step
                    'width': image_array.shape[1], # perform this step
                    'height': image_array.shape[0], # perform this step
                    'block_count': len(blocks) # perform this step
                } # perform this step
            } # perform this step
        
        except Exception as e: # handle errors from the try block
            print(f"Layout analysis error: {e}") # perform this step
            return self._fallback_layout_analysis(image_array) # return this value
```

### Snippet 2: `LayoutAnalyzer._build_hierarchy`
- Lines `196-207`
- Purpose: construct reading-order hierarchy from detected layout blocks.

```python
    def _build_hierarchy(self, blocks, image_shape): # define the function
        """Build reading order hierarchy""" # perform this step
        # Sort by position (top-to-bottom, left-to-right)
        sorted_blocks = sorted(blocks, key=lambda b: (b['bbox'][1], b['bbox'][0])) # store this value
        
        # Add reading order
        for idx, block in enumerate(sorted_blocks): # repeat for each item in the list
            block['reading_order'] = idx # store this value
        
        return sorted_blocks # return this value
```

### Snippet 3: `detect_connectors` endpoint
- Lines `875-930`
- Purpose: API endpoint that detects connectors and returns an adjacency graph for diagram analysis.

```python
@app.route('/api/v1/scan/connectors', methods=['POST']) # store this value
def detect_connectors(): # define the function
    """ # perform this step
    Detect connector lines and build adjacency graph # perform this step
    Useful for flowchart and diagram analysis # perform this step
    """ # perform this step
    try: # try this block and catch errors
        if 'image' not in request.files: # check condition
            return jsonify({'error': 'No image provided'}), 400 # return this value
        
        image_file = request.files['image'] # store this value
        
        # Read image
        image_bytes = image_file.read() # store this value
        image_array = cv2.imdecode( # store this value
            np.frombuffer(image_bytes, np.uint8), # perform this step
            cv2.IMREAD_COLOR # perform this step
        ) # perform this step
        
        if image_array is None: # check condition
            return jsonify({'error': 'Invalid image format'}), 400 # return this value
        
        # Binarize
        binarizer = AdaptiveBinarizer() # store this value
        binary = binarizer.binarize(image_array) # store this value
        
        # Detect shapes first
        tracer = SmartShapeTracer() # store this value
        shapes = tracer.trace_shapes(binary) # store this value
        
        # Trace connectors
        connector_tracer = ConnectorTracer() # store this value
        connector_results = connector_tracer.trace_connectors(binary, shapes) # store this value
        
        # Convert graph to JSON-serializable format
        graph_json = {str(k): v for k, v in connector_results['graph'].items()} # store this value
        
        return jsonify({ # return this value
            'success': True, # perform this step
            'connector_count': len(connector_results['connectors']), # perform this step
            'connection_count': connector_results['connection_count'], # perform this step
            'shape_count': len(shapes), # perform this step
            'graph': graph_json, # perform this step
            'graph_nodes': len(shapes), # perform this step
            'graph_edges': connector_results['connection_count'], # perform this step
            'connectors': [ # perform this step
                { # perform this step
                    'start': c['start'], # perform this step
                    'end': c['end'], # perform this step
                    'type': c['type'] # perform this step
                } # perform this step
                for c in connector_results['connectors'] # perform this step
            ] # perform this step
        }) # perform this step
    
    except Exception as e: # handle errors from the try block
        return jsonify({'error': str(e)}), 500 # return this value
```

### File
- `c:\Users\mlenj\Music\DOCUGRAPH_WEBSITE\backend\advanced_image_processing.py`

### Snippet 4: `ConnectorTracer.trace_connectors`
- Lines `365-410`
- Purpose: extract connector segments and link them to nearest shapes for adjacency graph construction.

```python
    def trace_connectors(self, binary_image, shapes): # define the function
        """ # perform this step
        Extract connector lines and build adjacency graph # perform this step
        
        Args: # perform this step
            binary_image: Binary image (0 or 255) # perform this step
            shapes: List of shape dicts from SmartShapeTracer # perform this step
        
        Returns: # perform this step
            dict with: # open a context block
                'connectors': list of line segments # perform this step
                'graph': adjacency list # perform this step
                'connections': list of (shape1_idx, shape2_idx, connector_type) # perform this step
        """ # perform this step
        connectors = self._extract_thin_lines(binary_image, shapes) # store this value
        
        # Build shape bounding boxes for matching
        shape_bboxes = [(s['bbox'], i) for i, s in enumerate(shapes)] # store this value
        
        # Match endpoints to shapes
        connections = [] # store this value
        for connector in connectors: # repeat for each item in the list
            start, end, line_type = connector['start'], connector['end'], connector['type'] # store this value
            
            # Find two nearest shapes
            nearest_shapes = self._find_nearest_shapes(start, end, shape_bboxes, k=2) # store this value
            
            if len(nearest_shapes) == 2: # check condition
                shape1_idx, shape2_idx = nearest_shapes # store this value
                connections.append({ # add this item to the result list
                    'from': shape1_idx, # perform this step
                    'to': shape2_idx, # perform this step
                    'connector': connector, # perform this step
                    'type': line_type # perform this step
                }) # perform this step
        
        # Build adjacency graph
        graph = self._build_adjacency_graph(len(shapes), connections) # store this value
        
        return { # return this value
            'connectors': connectors, # perform this step
            'connections': connections, # perform this step
            'graph': graph, # perform this step
            'connection_count': len(connections) # perform this step
        } # perform this step
```

### Snippet 5: `ConnectorTracer._extract_thin_lines`
- Lines `411-445`
- Purpose: isolate thin horizontal and vertical connector lines from the binarized image.

```python
    def _extract_thin_lines(self, binary_image, shapes, max_thickness=8): # define the function
        """Extract thin horizontal and vertical lines""" # perform this step
        connectors = [] # store this value
        
        # Horizontal lines
        kernel_h = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 1)) # store this value
        h_lines = cv2.morphologyEx(binary_image, cv2.MORPH_OPEN, kernel_h) # store this value
        
        # Vertical lines
        kernel_v = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 20)) # store this value
        v_lines = cv2.morphologyEx(binary_image, cv2.MORPH_OPEN, kernel_v) # store this value
        
        # Extract line coordinates
        h_contours, _ = cv2.findContours(h_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE) # store this value
        for contour in h_contours: # repeat for each item in the list
            x, y, w, h = cv2.boundingRect(contour) # store this value
            if w > 10:  # Min length
                connectors.append({ # add this item to the result list
                    'start': (x, y + h // 2),
                    'end': (x + w, y + h // 2),
                    'type': 'horizontal' # perform this step
                }) # perform this step
        
        v_contours, _ = cv2.findContours(v_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE) # store this value
        for contour in v_contours: # repeat for each item in the list
            x, y, w, h = cv2.boundingRect(contour) # store this value
            if h > 10:  # Min length
                connectors.append({ # add this item to the result list
                    'start': (x + w // 2, y),
                    'end': (x + w // 2, y + h),
                    'type': 'vertical' # perform this step
                }) # perform this step
        
        return connectors # return this value
```

### Snippet 6: `ConnectorTracer._find_nearest_shapes` and `_build_adjacency_graph`
- Lines `446-474`
- Purpose: match connector endpoints to neighboring shapes and produce undirected adjacency lists.

```python
    def _find_nearest_shapes(self, start_point, end_point, shape_bboxes, k=2): # define the function
        """Find k nearest shapes to line endpoints""" # perform this step
        distances = [] # store this value
        
        for bbox, idx in shape_bboxes: # repeat for each item in the list
            x1, y1, x2, y2 = bbox # store this value
            center = ((x1 + x2) / 2, (y1 + y2) / 2) # store this value
            
            # Distance from center to start and end
            dist_start = np.sqrt((start_point[0] - center[0]) ** 2 + (start_point[1] - center[1]) ** 2) # store this value
            dist_end = np.sqrt((end_point[0] - center[0]) ** 2 + (end_point[1] - center[1]) ** 2) # store this value
            avg_dist = (dist_start + dist_end) / 2 # store this value
            
            distances.append((avg_dist, idx)) # add this item to the result list
        
        distances.sort() # perform this step
        return [idx for _, idx in distances[:k]] # return this value
    
    def _build_adjacency_graph(self, num_shapes, connections): # define the function
        """Build adjacency list from connections""" # perform this step
        graph = defaultdict(list) # store this value
        
        for conn in connections: # repeat for each item in the list
            from_idx = conn['from'] # store this value
            to_idx = conn['to'] # store this value
            graph[from_idx].append(to_idx) # add this item to the result list
            graph[to_idx].append(from_idx) # add this item to the result list
        
        return dict(graph) # return this value
```

## Shared Component — WordLevelOCREngine

### Files
- `c:\Users\mlenj\Music\Docugraph_CnnOnly\backend\advanced_image_processing.py`
- `c:\Users\mlenj\Music\DOCUGRAPH_WEBSITE\backend\advanced_image_processing.py`
- Lines `481-625`
- Note: this OCR class is identical in both systems and is included once as a shared component.

### Purpose
- Purpose: perform word-level OCR on detected text-like components, crop and upscale regions, and return recognized text with confidence scores.

```python
# Word-Level OCR Engine
# ===========================

class WordLevelOCREngine: # define the class
    """ # perform this step
    Advanced OCR with word-level processing: # open a context block
    - Detects text components # perform this step
    - Crops word-sized regions # perform this step
    - 3× upscaling for better recognition # perform this step
    - Parallel processing (up to 4 workers) # perform this step
    - PSM 8 (single word mode) # perform this step
    """ # perform this step
    
    def __init__(self, num_workers=4, scale_factor=3, use_tesseract=True): # define the function
        """ # perform this step
        Args: # perform this step
            num_workers: Number of parallel OCR workers # perform this step
            scale_factor: Image scale-up factor (3× = 3) # store this value
            use_tesseract: Use Tesseract (True) or fallback to EasyOCR (False) # perform this step
        """ # perform this step
        self.num_workers = num_workers # store this value
        self.scale_factor = scale_factor # store this value
        self.use_tesseract = use_tesseract # store this value
        self.lock = threading.Lock() # store this value
    
    def extract_words(self, image, components, use_parallel=True): # define the function
        """ # perform this step
        Extract text from word-level components with OCR # open a context block
        
        Args: # perform this step
            image: Original image (BGR) # perform this step
            components: List of components from PixelScanner # perform this step
            use_parallel: Use parallel processing # perform this step
        
        Returns: # perform this step
            List of OCR results with text, confidence, bbox # open a context block
        """ # perform this step
        # Filter text-like components
        text_components = [c for c in components if c['type'] in ['text', 'connector']] # store this value
        
        if not text_components: # check condition
            return [] # return this value
        
        # Prepare crops
        crops = [] # store this value
        for comp in text_components: # repeat for each item in the list
            x_min, y_min, x_max, y_max = comp['bbox'] # store this value
            
            # Add padding
            pad = 2 # store this value
            x_min = max(0, x_min - pad) # store this value
            y_min = max(0, y_min - pad) # store this value
            x_max = min(image.shape[1], x_max + pad) # store this value
            y_max = min(image.shape[0], y_max + pad) # store this value
            
            # Crop region
            crop = image[y_min:y_max, x_min:x_max] # store this value
            
            # Upscale 3×
            if crop.shape[0] > 0 and crop.shape[1] > 0: # check condition
                scaled = cv2.resize(crop, None, fx=self.scale_factor, fy=self.scale_factor,  # store this value
                                   interpolation=cv2.INTER_CUBIC) # store this value
                
                # Stretch contrast
                lab = cv2.cvtColor(scaled, cv2.COLOR_BGR2LAB) # store this value
                l_channel = lab[:, :, 0] # store this value
                l_min, l_max = l_channel.min(), l_channel.max() # store this value
                if l_max > l_min: # check condition
                    l_channel = ((l_channel - l_min) * 255 / (l_max - l_min)).astype(np.uint8) # store this value
                    lab[:, :, 0] = l_channel # store this value
                    scaled = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR) # store this value
                
                crops.append({ # add this item to the result list
                    'image': scaled, # perform this step
                    'original_bbox': (x_min, y_min, x_max, y_max), # perform this step
                    'component': comp # perform this step
                }) # perform this step
        
        # Process crops
        if use_parallel and len(crops) > 1: # check condition
            results = self._process_crops_parallel(crops) # store this value
        else: # handle the alternate case
            results = self._process_crops_sequential(crops) # store this value
        
        return results # return this value
    
    def _process_crops_parallel(self, crops): # define the function
        """Process crops in parallel""" # perform this step
        results = [] # store this value
        
        with ThreadPoolExecutor(max_workers=self.num_workers) as executor: # open a context block
            future_to_crop = {executor.submit(self._ocr_crop, crop): crop for crop in crops} # store this value
            
            for future in as_completed(future_to_crop): # repeat for each item in the list
                try: # try this block and catch errors
                    result = future.result() # store this value
                    if result: # check condition
                        results.append(result) # add this item to the result list
                except Exception as e: # handle errors from the try block
                    print(f"⚠ Error processing crop: {e}") # perform this step
        
        return results # return this value
    
    def _process_crops_sequential(self, crops): # define the function
        """Process crops sequentially""" # perform this step
        results = [] # store this value
        
        for crop in crops: # repeat for each item in the list
            try: # try this block and catch errors
                result = self._ocr_crop(crop) # store this value
                if result: # check condition
                    results.append(result) # add this item to the result list
            except Exception as e: # handle errors from the try block
                print(f"⚠ Error processing crop: {e}") # perform this step
        
        return results # return this value
    
    def _ocr_crop(self, crop_data): # define the function
        """Run OCR on single crop""" # perform this step
        image = crop_data['image'] # store this value
        original_bbox = crop_data['original_bbox'] # store this value
        component = crop_data['component'] # store this value
        
        try: # try this block and catch errors
            if self.use_tesseract: # check condition
                # Use Tesseract PSM 8 (single word)
                config = '--psm 8 --oem 3' # store this value
                text = pytesseract.image_to_string(image, config=config).strip() # store this value
                conf = self._estimate_confidence(text) # store this value
            else: # handle the alternate case
                # Fallback: use basic image statistics
                text = "" # store this value
                conf = 0.5 # store this value
            
            if text: # check condition
                return { # return this value
                    'text': text, # perform this step
                    'confidence': conf, # perform this step
                    'bbox': original_bbox, # perform this step
                    'component_type': component['type'], # perform this step
                    'component_bbox': component['bbox'] # perform this step
                } # perform this step
        except Exception as e: # handle errors from the try block
            print(f"⚠ Tesseract error: {e}") # perform this step
        
        return None # return this value
    
    def _estimate_confidence(self, text): # define the function
        """Simple confidence estimation""" # perform this step
        if not text: # check condition
            return 0.0 # return this value
        # More text length suggests higher confidence (simple heuristic)
        return min(0.95, 0.5 + len(text) * 0.05) # return this value
```
```
