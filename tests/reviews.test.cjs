const test=require('node:test'),assert=require('node:assert/strict');
const {filterStories,initialFilters,filterUrl,storyCard}=require('../assets/reviews.js');
const stories=[
  {slug:'anthem',title:'2017 Entegra Anthem Review',text:'We loved the heated floors.',stock:'14931',year:2017,brand:'Entegra Coach',model:'Anthem',type:'Diesel Pusher',buyer:'McFarland’s',location:'Allen, Texas',date:'',dateLabel:''},
  {slug:'thor',title:'2016 Thor Chateau Review',text:'Our first RV.',stock:'TEST44',year:2016,brand:'Thor Motor Coach',model:'Chateau',type:'Class C',buyer:'Smith',location:'Austin, Texas',date:'2019-04',dateLabel:'April 2019'},
  {slug:'forest',title:'Forest River Georgetown',text:'Excellent experience.',stock:'TEST55',brand:'Forest River',model:'Georgetown',type:'Class A',buyer:'Jones',location:'Oregon',date:'',dateLabel:''}
];
test('stock, buyer, location and review body remain searchable',()=>{
  for(const q of ['14931','mcfarlands','heated floors','Allen Texas'])assert.deepEqual(filterStories(stories,{q}).map(s=>s.slug),['anthem']);
});
test('brand and RV type filters combine without broadening',()=>{
  assert.deepEqual(filterStories(stories,{brand:'Entegra',type:'Diesel Pusher'}).map(s=>s.slug),['anthem']);
  assert.deepEqual(filterStories(stories,{brand:'Entegra Coach',type:'Class C'}),[]);
  assert.deepEqual(filterStories(stories,{brand:'Thor'}).map(s=>s.slug),['thor']);
});
test('inventory brand deep link initializes a real dropdown filter',()=>{
  assert.deepEqual(initialFilters('?brand=Entegra%20Coach',stories),{q:'',brand:'Entegra Coach',type:''});
  assert.deepEqual(initialFilters('?brand=Thor',stories),{q:'',brand:'Thor Motor Coach',type:''});
});
test('clearing brand URL yields all stories rather than reinstating brand',()=>{
  const url=filterUrl('https://example.com/reviews.html?brand=Entegra&q=Anthem&utm_source=sample',{});
  assert.equal(url.search,'?utm_source=sample');
  const filters=initialFilters(url.search,stories);
  assert.deepEqual(filters,{q:'',brand:'',type:''});
  assert.equal(filterStories(stories,filters).length,3);
});
test('query changes are shareable and maintain unrelated attribution',()=>{
  const url=filterUrl('https://example.com/reviews.html?brand=Entegra&utm_source=sample',{q:'14931',brand:'',type:'Diesel Pusher'});
  assert.equal(url.searchParams.get('q'),'14931');assert.equal(url.searchParams.get('brand'),null);assert.equal(url.searchParams.get('utm_source'),'sample');
});
test('story cards preserve stock and escape source HTML',()=>{
  const card=storyCard({...stories[0],title:'<script>alert(1)</script>',text:'<img onerror=x>'});
  assert.ok(card.includes('Stock #14931'));assert.ok(card.includes('&lt;script&gt;'));assert.ok(!card.includes('<img onerror'));assert.ok(!card.includes('★★★★★'));
});

test('Google display preserves low ratings, full text and every provider attribution',()=>{
  const {googlePlace}=require('../assets/reviews.js');
  const html=googlePlace({name:'Example dealer',rating:4.3,count:20,url:'https://maps.google.com/example',attributions:[{provider:'Example data provider',url:'https://example.com/attribution'}],reviews:[{rating:2,author:'Real reviewer',authorUrl:'https://example.com/author',authorPhoto:'https://example.com/avatar.jpg',url:'https://maps.google.com/review',text:'Full original review. <script>',date:'a month ago'}]},'../');
  assert.ok(html.includes('2 out of 5 stars'));assert.ok(html.includes('Full original review. &lt;script&gt;'));assert.ok(html.includes('Example data provider'));assert.ok(html.includes('https://example.com/attribution'));assert.ok(html.includes('../assets/google-maps-attribution.svg'));assert.ok(html.includes('alt="Google Maps"'));assert.ok(html.includes('https://maps.google.com/review'));assert.ok(html.includes('https://example.com/author'));assert.ok(html.includes('https://example.com/avatar.jpg'));
});
