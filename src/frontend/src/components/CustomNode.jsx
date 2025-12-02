/* Copied of PoC-Robert-React-Flow */
import { Handle, Position } from '@xyflow/react';
import { useRef, useLayoutEffect, useState } from 'react';

export function CustomNode({ data, isConnectable, selected }) {
  const nodeBackground = data.background || '#fff';
  const distance = data.distance ?? null;
  const contentRef = useRef(null);
  const [contentHeight, setContentHeight] = useState(80); // Default height
  
  // Measure content height on mount and when data changes
  useLayoutEffect(() => {
    if (contentRef.current) {
      const height = contentRef.current.offsetHeight;
      setContentHeight(height);
    }
  }, [data.label]); // Re-measure if label changes
  
  // Determine visual state based on distance
  const isSelected = distance === 0;
  const isDistant = distance !== null && distance > 1;
  
  // Calculate scaling - 130% for selected nodes
  const scale = isSelected ? 1.3 : 1.0;
  
  // Base dimensions (inner content size)
  const baseWidth = data.width || 160;
  
  // Wrapper dimensions match the visual size after scaling
  const wrapperWidth = baseWidth * scale;
  const wrapperHeight = contentHeight * scale;
  
  // Calculate styling
  const fontWeight = isSelected ? 'bold' : (data.fontWeight || 'normal');
  const zIndex = isSelected ? 1000 : 'auto';
  
  // Distant node styling - using CSS variables
  const textColor = isDistant ? 'var(--distant-node-text-color)' : (data.color || '#000');
  const background = isDistant ? 'var(--distant-node-background-color)' : nodeBackground;

  return (
    <div
      className="custom-node-wrapper"
      style={{
        width: wrapperWidth,
        height: wrapperHeight,
        position: 'relative',
        transition: 'width 300ms ease-out, height 300ms ease-out',
        zIndex,
      }}
    >
      {/* Handles on all four sides - attached to wrapper */}
      <Handle
        type="source"
        position={Position.Top}
        id="top"
        isConnectable={isConnectable}
        className="opacity-0 pointer-events-none"
      />
      <Handle
        type="source"
        position={Position.Right}
        id="right"
        isConnectable={isConnectable}
        className="opacity-0 pointer-events-none"
      />
      <Handle
        type="source"
        position={Position.Bottom}
        id="bottom"
        isConnectable={isConnectable}
        className="opacity-0 pointer-events-none"
      />
      <Handle
        type="source"
        position={Position.Left}
        id="left"
        isConnectable={isConnectable}
        className="opacity-0 pointer-events-none"
      />
      
      {/* Target handles on all sides */}
      <Handle
        type="target"
        position={Position.Top}
        id="target-top"
        isConnectable={isConnectable}
        className="opacity-0 pointer-events-none"
      />
      <Handle
        type="target"
        position={Position.Right}
        id="target-right"
        isConnectable={isConnectable}
        className="opacity-0 pointer-events-none"
      />
      <Handle
        type="target"
        position={Position.Bottom}
        id="target-bottom"
        isConnectable={isConnectable}
        className="opacity-0 pointer-events-none"
      />
      <Handle
        type="target"
        position={Position.Left}
        id="target-left"
        isConnectable={isConnectable}
        className="opacity-0 pointer-events-none"
      />

      {/* Inner content div - centered and scaled */}
      <div
        ref={contentRef}
        className="custom-node"
        style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: `translate(-50%, -50%) scale(${scale})`,
          transformOrigin: 'center center',
          width: baseWidth,
          color: textColor,
          border: selected
            ? '3px solid #1a73e8'
            : data.border || '1px solid #000',
          borderRadius: data.borderRadius || '3px',
          fontSize: data.fontSize || '12px',
          fontWeight,
          whiteSpace: data.whiteSpace || 'normal',
          boxShadow: selected
            ? '0 0 0 2px rgba(26, 115, 232, 0.2), 0 4px 12px rgba(0, 0, 0, 0.15)'
            : data.boxShadow || 'none',
          transition: 'color 300ms ease-out, font-weight 300ms ease-out, transform 300ms ease-out',
        }}
      >
        {/* Flexbox container with drag handle and content */}
        <div className="flex h-full">
          {/* First child: Drag Handle - fixed width */}
          <div
            className="group/handle flex items-center justify-center cursor-move hover:brightness-[0.85] transition-[filter] duration-200 w-6 shrink-0"
            style={{
              background,
              borderTopLeftRadius: data.borderRadius || '3px',
              borderBottomLeftRadius: data.borderRadius || '3px',
            }}
          >
            <div className="flex flex-col gap-0.5">
              <div className="w-[3px] h-[3px] bg-black/30 rounded-full transition-[width] duration-500 ease-in-out group-hover/handle:w-[15px]" />
              <div className="w-[3px] h-[3px] bg-black/30 rounded-full transition-[width] duration-500 ease-in-out group-hover/handle:w-[15px]" />
              <div className="w-[3px] h-[3px] bg-black/30 rounded-full transition-[width] duration-500 ease-in-out group-hover/handle:w-[15px]" />
            </div>
          </div>

          {/* Second child: Content - takes remaining space */}
          <div
            className="nodrag text-left flex-1 cursor-default"
            style={{
              padding: data.padding || '10px',
              background,
              borderTopRightRadius: data.borderRadius || '3px',
              borderBottomRightRadius: data.borderRadius || '3px',
            }}
          >
            {data.label}
          </div>
        </div>
      </div>
    </div>
  );
}