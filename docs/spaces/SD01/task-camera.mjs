import {fitCamera,constrainCamera} from './state.mjs';
/** Reserve a rectangle beside the measured task card. All values are CSS pixels.
 * Caller supplies actual getBoundingClientRect() edges and measured top chrome.
 * No DOM access, animation, or GPU behavior is hidden in this function.
 */
export function taskSafeViewport(width,height,card,{layout,topInset=0,margin=16}={}){
 const values=[width,height,card?.left,card?.right,card?.top,card?.bottom,topInset,margin];
 if(!values.every(Number.isFinite)||width<=0||height<=0||margin<0||topInset<0||card.right<card.left||card.bottom<card.top||!['left','bottom'].includes(layout))throw new RangeError('Invalid task viewport input');
 const x=layout==='left'?Math.max(margin,Math.min(width,card.right)+margin):margin;
 const y=Math.max(margin,Math.min(height,topInset)+margin);
 const right=width-margin,bottom=layout==='bottom'?Math.min(height-margin,card.top-margin):height-margin;
 const safe={x,y,width:right-x,height:bottom-y};
 if(safe.width<24||safe.height<24)throw new RangeError('Insufficient unobscured viewport: collapse task card or use text mode');
 return safe;
}
/** Fit to the reserved rectangle then use the same world-height guard as the app.
 * Returned view is applied with PerspectiveCamera.setViewOffset(...).
 * clearViewOffset() is required on full-view exit. Recompute on resize/layout.
 */
export function fitTaskCamera({position,target,bounds,worldBounds,worldMaxY,fov,width,height,safe}){
 if(![width,height,fov,safe?.x,safe?.y,safe?.width,safe?.height].every(Number.isFinite)||width<=0||height<=0||safe.width<=0||safe.height<=0||safe.x<0||safe.y<0||safe.x+safe.width>width||safe.y+safe.height>height||fov<=0||fov>=170)throw new RangeError('Invalid task camera input');
 const verticalFov=2*Math.atan(Math.tan(fov*Math.PI/360)*safe.height/height)*180/Math.PI;
 const fitted=fitCamera(position,target,bounds,verticalFov,safe.width/safe.height);
 const bounded=constrainCamera(fitted.position,fitted.target,worldBounds,worldMaxY);
 return {...bounded,view:{fullWidth:width,fullHeight:height,offsetX:width/2-(safe.x+safe.width/2),offsetY:height/2-(safe.y+safe.height/2),width,height},safe};
}
