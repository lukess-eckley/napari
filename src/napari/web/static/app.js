const viewerTitle = document.getElementById("viewer-title");
const viewerStatus = document.getElementById("viewer-status");
const viewerTheme = document.getElementById("viewer-theme");
const viewerNDisplay = document.getElementById("viewer-ndisplay");
const viewerAxes = document.getElementById("viewer-axes");
const viewerStep = document.getElementById("viewer-step");
const viewerCanvas = document.getElementById("viewer-canvas");
const layersContainer = document.getElementById("layers");

async function fetchViewerState() {
  try {
    const response = await fetch("api/viewer");
    if (!response.ok) {
      throw new Error(`Request failed with status ${response.status}`);
    }
    const payload = await response.json();
    renderViewer(payload);
    viewerStatus.textContent = "Connected";
    viewerStatus.className = "status-ok";
  } catch (error) {
    viewerStatus.textContent = `Unable to reach napari: ${error.message}`;
    viewerStatus.className = "status-error";
  }
}

function renderViewer(payload) {
  viewerTitle.textContent = payload.title ?? "napari Viewer";
  viewerTheme.textContent = payload.theme ?? "–";
  viewerNDisplay.textContent = payload.ndisplay ?? "–";
  viewerAxes.textContent = (payload.axis_labels || []).join(", ") || "–";
  viewerStep.textContent = (payload.current_step || []).join(", ") || "–";
  viewerCanvas.textContent = (payload.canvas_size || []).join(" × ") || "–";

  const list = document.createElement("div");
  list.className = "layers-list";

  (payload.layers || []).forEach((layer) => {
    const card = document.createElement("article");
    card.className = "layer-card";

    const heading = document.createElement("h3");
    heading.textContent = `${layer.name || "(unnamed)"} (${layer.type || "Layer"})`;
    card.appendChild(heading);

    const items = document.createElement("ul");
    items.innerHTML = `
      <li><strong>Visible:</strong> ${layer.visible ? "yes" : "no"}</li>
      <li><strong>Opacity:</strong> ${layer.opacity ?? "–"}</li>
      <li><strong>Dimensions:</strong> ${layer.ndim ?? "–"}</li>
      <li><strong>Shape:</strong> ${(layer.shape || []).join(" × ") || "–"}</li>
      <li><strong>Data type:</strong> ${layer.dtype || "–"}</li>
      <li><strong>Scale:</strong> ${(layer.scale || []).join(", ") || "–"}</li>
      <li><strong>Translate:</strong> ${(layer.translate || []).join(", ") || "–"}</li>
    `;

    if (layer.metadata && Object.keys(layer.metadata).length) {
      const metadata = document.createElement("li");
      metadata.innerHTML = `<strong>Metadata:</strong> <pre>${JSON.stringify(
        layer.metadata,
        null,
        2
      )}</pre>`;
      items.appendChild(metadata);
    }

    if (layer.extent && layer.extent.length) {
      const extent = document.createElement("li");
      extent.innerHTML = `<strong>Extent:</strong> ${layer.extent
        .map((point) => point.join(", "))
        .join(" to ")}`;
      items.appendChild(extent);
    }

    card.appendChild(items);

    const source = document.createElement("small");
    if (layer.source && (layer.source.path || layer.source.sample)) {
      const parts = [];
      if (layer.source.path) {
        parts.push(`path: ${layer.source.path}`);
      }
      if (layer.source.sample) {
        parts.push(`sample: ${layer.source.sample}`);
      }
      source.textContent = `Source → ${parts.join("; ")}`;
    } else {
      source.textContent = "Source → session";
    }
    card.appendChild(source);

    list.appendChild(card);
  });

  layersContainer.innerHTML = "";
  layersContainer.appendChild(list);
}

fetchViewerState();
setInterval(fetchViewerState, 2000);
