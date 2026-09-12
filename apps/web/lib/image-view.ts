export function fitImage(imageWidth: number, imageHeight: number, viewportWidth: number, viewportHeight: number) {
  if (imageWidth <= 0 || imageHeight <= 0 || viewportWidth <= 0 || viewportHeight <= 0) return { width: 0, height: 0 };
  const scale = Math.min(viewportWidth / imageWidth, viewportHeight / imageHeight, 1);
  return { width: imageWidth * scale, height: imageHeight * scale };
}

export const imageZoomLevels = [1, 1.5, 2, 3, 4];
