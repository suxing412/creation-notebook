import {test,expect} from '@playwright/test';
import {instrument,openCity,state,settled,selectZone,zones,assertFullCity,assertHealthy,attachEvidence} from './helpers.mjs';
import {displayGroundId as id} from '../../docs/cities/luoyang/ground-content.mjs';
test('display-only ground survives every zone without replacing city models; research remains independent',async({page},info)=>{
 const evidence=await instrument(page);await page.emulateMedia({reducedMotion:'reduce'});
 try{
  await openCity(page,info.project.name==='mobile');const first=await state(page);expect(first.modelNodeIds).toHaveLength(87);expect(first.modelNodeIds).toContain(id);
  const ids=[...first.modelNodeIds].sort();for(const z of zones){const s=await selectZone(page,z.id,info.project.name==='mobile');expect([...s.modelNodeIds].sort()).toEqual(ids);assertFullCity(s);expect(s.sceneRevision).toBe(first.sceneRevision);}
  await page.locator('.pj-chapters [data-ch="ritual"]').click();await expect.poll(async()=>(await state(page)).studyId).not.toBeNull();expect((await settled(page)).modelNodeIds).not.toContain(id);
  expect((await selectZone(page,'Z13',info.project.name==='mobile')).modelNodeIds).toEqual(first.modelNodeIds);
  const canvas=page.locator('#pj-canvas'),box=await canvas.boundingBox();if(info.project.name==='mobile')await canvas.tap({position:{x:box.width*.5,y:box.height*.65}});else await page.mouse.click(box.x+box.width*.5,box.y+box.height*.65);
  // Ground cannot become the picked model. Presence is separately proved by the complete runtime membership.
  await expect(page.locator('#pj-note')).not.toContainText('全城连续展示地表');
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBe(true);assertHealthy(evidence);
 }finally{await attachEvidence(page,info,evidence,{notHardwareGPUCertification:true});}
});
