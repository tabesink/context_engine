type PositionedNode = {
  id: string;
  degree?: number;
};

export function buildVisualizationLayout(nodes: PositionedNode[]) {
  const count = Math.max(nodes.length, 1);
  const radius = Math.max(6, Math.sqrt(count) * 3);
  const positions: Record<string, { x: number; y: number }> = {};
  nodes.forEach((node, index) => {
    const angle = (Math.PI * 2 * index) / count;
    const wobble = node.degree ? Math.min(node.degree * 0.02, 1.5) : 0;
    positions[node.id] = {
      x: Math.cos(angle) * (radius + wobble),
      y: Math.sin(angle) * (radius + wobble),
    };
  });
  return { positions };
}
