import test from 'node:test';
import assert from 'node:assert/strict';
import { groundInputVelocity, groundToWorld, worldToGround, stepGroundVelocity, constrainGroundStep, smoothOrbitOffset } from '../docs/cities/luoyang/ground-navigation.mjs';
const close = (a,b,epsilon=1e-8) => assert.ok(Math.abs(a-b)<epsilon, `${a} differs from ${b}`);
const length = v => Math.hypot(...v);
const frames = [10,15,20,30,60,90,120,144];

test('the same one-second key press travels equally at 10–144 updates per second', () => {
  const outputs = frames.map(fps => {
    let velocity=[0,0,0], position=[0,60,-80], target=[0,0,0];
    for(let i=0;i<fps;i++) {
      const step=stepGroundVelocity(velocity,groundInputVelocity(position,target,new Set(['KeyW'])),1/fps);
      velocity=step.velocity;
      const travel=groundToWorld(step.delta,position,target);
      position=position.map((v,j)=>v+travel[j]); target=target.map((v,j)=>v+travel[j]);
    }
    close(target[1],0); close(position[1],60);
    return { distance: target[2], speed:length(velocity) };
  });
  const expected=22*(1-0.075*(1-Math.exp(-1/0.075)));
  for(const output of outputs) { close(output.distance,expected); close(output.speed,outputs[0].speed); }
});

test('screen-relative direction, normalized diagonals, opposite keys and speed limits', () => {
  const keys=(...names)=>new Set(names.map(k=>'Key'+k));
  const groundVelocity=(p,t,k)=>groundToWorld(groundInputVelocity(p,t,k),p,t);
  assert.deepEqual(groundVelocity([0,60,-80],[0,0,0],keys('W')),[0,0,22]);
  assert.deepEqual(groundVelocity([0,60,-80],[0,0,0],keys('D')),[-22,0,0]);
  assert.deepEqual(groundVelocity([-80,60,0],[0,0,0],keys('W')),[22,0,0]);
  close(length(groundVelocity([0,60,-80],[0,0,0],keys('W','D'))),22);
  close(length(groundVelocity([0,60,-80],[0,0,0],keys('W','S','A','D'))),0);
  close(length(groundVelocity([0,0.1,-0.1],[0,0,0],keys('W'))),2);
  close(length(groundVelocity([0,60000,-80000],[0,0,0],keys('W'))),900);
});

test('acceleration and braking are smooth and converge without overshoot or reverse drift', () => {
  const first=stepGroundVelocity([0,0,0],[0,0,100],1/144);
  assert.ok(first.velocity[2]>0 && first.velocity[2]<10);
  close(stepGroundVelocity([0,0,0],[0,0,100],0).delta[2],0);
  for(const fps of frames) {
    let velocity=[0,0,900], distance=0, previous=900;
    for(let i=0;i<fps;i++) {
      const step=stepGroundVelocity(velocity,[0,0,0],1/fps);
      assert.ok(step.velocity[2]>=0 && step.velocity[2]<=previous);
      assert.ok(step.delta[2]>=0);
      velocity=step.velocity; previous=velocity[2]; distance+=step.delta[2];
    }
    assert.deepEqual(velocity,[0,0,0]); close(distance,900*.035,.001);
  }
});

test('ground bounds clip the allowed displacement and clear outward velocity', () => {
  const result=constrainGroundStep([9,0,-9],[3,0,-3],[20,0,-20],[-10,-10,10,10]);
  assert.deepEqual(result,{delta:[1,0,-1],velocity:[0,0,0]});
  assert.deepEqual(constrainGroundStep([10,0,-10],[-2,0,2],[-5,0,5],[-10,-10,10,10]),{delta:[-2,0,2],velocity:[-5,0,5]});
});

test('rotation and logarithmic zoom settle equally at 10–144 updates per second', () => {
  const outputs=frames.map(fps=>{
    let offset=[0,60,-80];
    for(let i=0;i<fps;i++) offset=smoothOrbitOffset(offset,[25,50,25],1/fps).offset;
    return offset;
  });
  for(const output of outputs) output.forEach((v,i)=>close(v,outputs[0][i],.001));
  assert.deepEqual(smoothOrbitOffset([1,2,3],[1,2,3],1/60),{pending:false,offset:[1,2,3]});
});

test('rotation crosses the signed bearing seam by the short arc', () => {
  const offset=yaw=>[100*Math.sin(yaw),100,100*Math.cos(yaw)];
  const result=smoothOrbitOffset(offset(179*Math.PI/180),offset(-179*Math.PI/180),.05);
  assert.ok(result.offset[2]<-99);
  assert.ok(result.offset.every(Number.isFinite));
});

test('held forward velocity follows the rendered heading with no stale world-direction component', () => {
  const position=[-80,60,0], target=[0,0,0], local=[0,0,22];
  const step=stepGroundVelocity(local,groundInputVelocity(position,target,new Set(['KeyW'])),1/60);
  const travel=groundToWorld(step.delta,position,target);
  close(travel[2],0); assert.ok(travel[0]>0);
  const clipped=constrainGroundStep([9,0,0],groundToWorld([0,0,4],position,target),groundToWorld(local,position,target),[-10,-10,10,10]);
  assert.deepEqual(worldToGround(clipped.velocity,position,target),[0,0,0]);
});

test('a straight-down interrupted flight retains a usable ground heading', () => {
  const world=groundToWorld([0,0,22],[0,100,0],[0,0,0],[-1,0]);
  assert.deepEqual(world,[-22,0,0]);
  assert.deepEqual(worldToGround(world,[0,100,0],[0,0,0],[-1,0]),[0,0,22]);
});
