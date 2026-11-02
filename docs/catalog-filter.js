export function matchesCatalogFilter(item, query='', kind='all') {
 const q=String(query).trim().normalize('NFKC').toLocaleLowerCase();
 return (kind==='all'||item.kind===kind||(kind==='methods'&&['recipe','method'].includes(item.kind)))&&String(item.search||'').normalize('NFKC').toLocaleLowerCase().includes(q);
}
