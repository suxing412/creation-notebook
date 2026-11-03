/** Only retire nodes inside original market root; never prefix-remove shared roofs or replacement roots. */
export function applyMarketReplacements(value,contract,flowPlan,flow='A'){
 const source=value.roots[0];if(!source)throw Error('Missing original market root');
 const retire=(ids,expected)=>{const wanted=new Set(ids),nodes=[];if(wanted.size!==expected)throw Error('Retirement contract duplicate/count');source.traverse(n=>{if(wanted.has(n.userData?.name||n.name))nodes.push(n)});if(nodes.length!==expected||new Set(nodes.map(n=>n.userData?.name||n.name)).size!==expected)throw Error('Source node identity mismatch; refusing overlapping replacement');for(const node of nodes){node.removeFromParent();value.roots.push(node)}return nodes.map(n=>n.userData?.name||n.name)};
 const removedN2=retire(contract.removeExactNodeIds,30),removedRoutes=flow==='B'?retire(flowPlan.retireOriginalNames,7):[];
 let remainingN2=0;source.traverse(n=>{if((n.userData?.name||n.name).startsWith('N2_'))remainingN2++});if(remainingN2)throw Error('Unexpected original N2 remains');
 value.assemblyEvidence={removedN2,removedRoutes,flow,roofVisibilityChanged:false};return value;
}
