import {matchesCatalogFilter as m} from '../../docs/catalog-filter.js';import assert from 'node:assert/strict';
const a={kind:'regular',search:'010 栖格 SLOT'};
assert.ok(m(a));assert.ok(m(a,'０１０'));assert.ok(m(a,' slot '));assert.ok(m(a,'栖格','regular'));assert.ok(!m(a,'010','fusion'));assert.ok(!m(a,'不存在'));assert.ok(!m(a,'','other'));assert.ok(!m(a,'<script>'));assert.ok(m({kind:'recipe',search:'翼'},'','methods'));assert.ok(m({kind:'method',search:'方法'},'','methods'));assert.ok(m({kind:'space-design',search:'SD01'},'sd01','space-design'));assert.ok(!m({kind:'fusion',search:'F02'},'f02','regular'));console.log('12 filter cases passed');

assert.ok(m({kind:'regular',search:'012 禾仓·前场 东汉 河南新密'},'东汉'));assert.ok(m({kind:'regular',search:'012 禾仓·前场 东汉 河南新密'},'河南'));
