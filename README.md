# uv_kit
Small uv utility collection

Currently found in the uv editor -> tool category

![grafik](https://user-images.githubusercontent.com/13512160/235482990-767823b4-f5c1-41f8-a93c-f279c74e9baf.png)


- Map channels: choose uv channel, added here for convenience. 
- Select Ring: selects uv edgerings from the current edge selection, +/- buttons to expand/shrink the uv edgering by one edge.
- Select Loop: selects uv edgeloops from the current edge selection, +/- buttons to expand/shrink the uv edgeloops by one edge.
- Align: aligns the uv loops on X/Y or use Auto to let it do a best guess. 
  
  > Shift aligns to maximum
  
  > Ctrl  aligns to minimum
  
  > Alt   makes it operate globally, across multiple objects
  
- Straighten: 
  
  > Even: distributes points inbetween start - end from each loop in even distances.
  
  > Geometry: distributes the points according to their distance in 3D space.
  
  > Project: distributes the points project from the current position to the line from start-end
  
- Constrained Unwrap: Keeps the selected uv's in place/pinned and unwraps the unselected rest of the uv island.

  > Shift - ignore seams
   
  > Ctrl  - ignore pins
   
  > Alt   - ignore seams and pins
