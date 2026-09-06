import os
os.environ['ARTIFACT_TOOL_RPC_DAEMON_STARTUP_TIMEOUT_S']='90'
from artifact_tool import Workbook, SpreadsheetFile
from itertools import product

recipes=[]
ingredients=[]
counter=1

def yn(x): return 'Yes' if x else 'No'

def add(cat,name,family,ings,method,prep=10,cook=20,serves=4,protein='',carb='',focus='',freezer=False,lunchbox=False,veg=False,onepot=False,swaps=''):
    global counter
    rid=f'GEN-RCP-{counter:04d}'; counter+=1
    recipes.append([rid,cat,name,family,serves,prep,cook,'$',protein,carb,focus,yn(freezer),yn(lunchbox),yn(veg),'Yes','Yes',yn(onepot),' | '.join(f'{i+1}. {s}' for i,s in enumerate(method)),swaps])
    for n,(iname,qty,unit,group,optional,swap_group) in enumerate(ings,1):
        ingredients.append([rid,n,iname,qty,unit,group,yn(optional),swap_group])

def take(a,b,n): return list(product(a,b))[:n]

# ---------- BREAKFAST 150 ----------
fruits=['banana','apple','pear','peach','mango','strawberry','blueberry','raspberry','pineapple','sultana']
for fruit,flav in take(fruits,['cinnamon','vanilla','honey'],30):
    add('Breakfast',f'{fruit.title()} {flav.title()} Overnight Oats','Overnight oats',
        [('rolled oats',2,'cup','grain',False,'Oats/Breakfast Grain'),('milk',2,'cup','liquid',False,'Milk'),(fruit,1.5,'cup','fruit',False,'Seasonal Fruit'),(flav,1,'tsp','flavour',False,'Sweetener/Flavour'),('chia seeds',2,'tbsp','seed',True,'Seeds')],
        ['Combine oats and milk.',f'Stir through {fruit} and {flav}.','Divide into containers.','Chill overnight.','Serve cold or warm.'],prep=8,cook=0,carb='oats',focus=fruit,lunchbox=True,veg=True,swaps='Swap any fresh, frozen or canned-in-juice fruit; use dairy or plant milk.')

addins=['banana','apple','blueberry','strawberry','pear','peach','sultana','choc chip','cinnamon','vanilla']
for x,flour in take(addins,['plain flour','wholemeal flour','oat flour'],30):
    add('Breakfast',f'{x.title()} {flour.replace(" flour","").title()} Pancakes','Pancakes',
        [(flour,2,'cup','flour',False,'Flour'),('baking powder',3,'tsp','raising',False,'Raising Agent'),('milk',1.5,'cup','liquid',False,'Milk'),('eggs',2,'each','protein',False,'Egg'),(x,1,'cup','add-in',False,'Fruit/Add-in'),('oil',1,'tbsp','fat',False,'Cooking Fat')],
        ['Mix dry ingredients.','Whisk milk and eggs.','Combine wet and dry.',f'Fold through {x}.','Cook small pancakes in a lightly oiled pan.'],protein='eggs',carb=flour,focus=x,lunchbox=True,veg=True,swaps='Use GF flour if needed; change fruit or flavour freely.')

vegs=['spinach','tomato','mushroom','capsicum','corn','peas','zucchini','broccoli','sweet potato','onion']
for v,fmt in take(vegs,['Scramble','Breakfast Muffins','Breakfast Wrap'],30):
    ings=[('eggs',8,'each','protein',False,'Egg'),(v,2,'cup','vegetable',False,'Flexible Vegetables'),('cheese',0.5,'cup','dairy',True,'Cheese'),('milk',0.25,'cup','liquid',True,'Milk')]
    if fmt=='Breakfast Wrap': ings.append(('wraps',4,'each','bread',False,'Wrap/Bread'))
    add('Breakfast',f'{v.title()} {fmt}','Egg breakfasts',ings,['Prepare the vegetable.','Whisk and cook eggs.','Combine egg and vegetables.','Add cheese if using.','Serve in the chosen format.'],protein='eggs',carb='wraps' if fmt=='Breakfast Wrap' else '',focus=v,freezer=fmt=='Breakfast Muffins',lunchbox=fmt!='Scramble',veg=True,swaps='Use leftover vegetables; cheese is optional and wraps can be GF.')

toppings=[('peanut butter','banana'),('ricotta','honey'),('avocado','tomato'),('baked beans','cheese'),('egg','spinach'),('cottage cheese','pineapple'),('apple','cinnamon'),('tuna','corn'),('hummus','cucumber'),('jam','yoghurt')]
for (a,b),fmt in take(toppings,['Toast','English Muffin','Breakfast Roll'],30):
    bread={'Toast':'bread','English Muffin':'English muffins','Breakfast Roll':'bread rolls'}[fmt]
    add('Breakfast',f'{a.title()} & {b.title()} {fmt}','Breakfast breads',[(bread,4,'serve','bread',False,'Wrap/Bread'),(a,1,'cup','topping',False,'Breakfast Topping'),(b,1,'cup','topping',False,'Fruit/Add-in')],['Toast or warm bread.',f'Prepare {a}.',f'Add {a}.',f'Top with {b}.','Serve.'],protein=a if a in ['egg','tuna'] else '',carb=bread,focus=b,lunchbox=True,veg=a!='tuna',swaps='Bread forms and toppings can be mixed across the whole family.')

bfl=['banana','apple cinnamon','blueberry','pear','peach','carrot','pumpkin','choc chip','sultana','berry']
for x,fmt in take(bfl,['Breakfast Muffins','Breakfast Slice','Baked Oat Cups'],30):
    base='rolled oats' if fmt=='Baked Oat Cups' else 'self-raising flour'
    add('Breakfast',f'{x.title()} {fmt}','Breakfast baking',[(base,2,'cup','grain/flour',False,'Flour/Oats'),('milk',1,'cup','liquid',False,'Milk'),('eggs',2,'each','protein',False,'Egg'),(x,1.5,'cup','add-in',False,'Fruit/Add-in'),('oil',0.33,'cup','fat',False,'Cooking Fat'),('brown sugar or honey',0.33,'cup','sweetener',True,'Sweetener/Flavour')],['Heat oven to 180°C.','Mix dry ingredients.','Mix wet ingredients.','Combine and fold through flavour.','Bake until set.'],protein='eggs',carb=base,focus=x,freezer=True,lunchbox=True,veg=True,swaps='Swap fruit/veg; reduce sweetener; use GF flour or certified GF oats.')

# ---------- LUNCH 150 ----------
fillings=[('Chicken Salad','chicken','lettuce'),('Tuna Corn','tuna','corn'),('Egg Lettuce','egg','lettuce'),('Ham Cheese','ham','cheese'),('Chickpea Crunch','chickpeas','carrot'),('Bean Salsa','beans','salsa'),('Hummus Veg','hummus','cucumber'),('Leftover Roast','leftover roast meat','carrot'),('Cheese Tomato','cheese','tomato'),('Lentil Slaw','lentils','cabbage')]
for (label,p,v),(fmt,bread) in take(fillings,[('Wrap','wraps'),('Sandwich','bread'),('Pocket','pita bread')],30):
    add('Lunch',f'{label} {fmt}','Wraps & sandwiches',[(bread,4,'serve','bread',False,'Wrap/Bread'),(p,2,'cup','protein',False,'Lunch Protein'),(v,2,'cup','produce',False,'Flexible Vegetables'),('salad leaves',2,'cup','produce',True,'Flexible Vegetables'),('spread or dressing',0.5,'cup','sauce',True,'Sauce')],['Prepare filling.','Open or warm bread.','Layer filling and vegetables.','Add spread.','Roll, close or cut.'],protein=p,carb=bread,focus=v,lunchbox=True,veg=p in ['egg','chickpeas','beans','hummus','cheese','lentils'],swaps='Any cooked protein or legumes can replace the filling; bread forms are interchangeable.')

prots=['chicken','beef mince','tuna','egg','tofu','chickpeas']
profiles=[('Mexican','salsa','corn'),('Teriyaki','teriyaki sauce','broccoli'),('Lemon Herb','lemon herb dressing','cucumber'),('Curry','mild curry sauce','peas'),('BBQ','BBQ sauce','carrot')]
for p,(style,sauce,v) in take(prots,profiles,30):
    add('Lunch',f'{style} {p.title()} Rice Bowl','Lunch bowls',[('rice',2,'cup dry','grain',False,'Rice/Grain'),(p,500,'g','protein',False,'Lunch Protein'),(v,2,'cup','produce',False,'Flexible Vegetables'),('mixed vegetables',2,'cup','produce',False,'Frozen/Seasonal Vegetables'),(sauce,0.5,'cup','sauce',False,'Sauce')],['Cook rice.',f'Cook or prepare {p}.','Cook vegetables.',f'Add {sauce}.','Serve over rice.'],protein=p,carb='rice',focus=v,lunchbox=True,veg=p in ['egg','tofu','chickpeas'],swaps='Swap rice for another grain or potato; frozen vegetables work well.')

soups=[('Tomato Lentil','lentils','tomato'),('Chicken Vegetable','chicken','mixed vegetables'),('Potato Corn','potato','corn'),('Pumpkin Chickpea','chickpeas','pumpkin'),('Minestrone Bean','beans','mixed vegetables'),('Pea Ham','ham','peas')]
for (label,p,v),style in take(soups,['Classic Soup','Thick Soup','Noodle Soup','Rice Soup','One-Pot Soup'],30):
    carb='noodles' if style=='Noodle Soup' else ('rice' if style=='Rice Soup' else 'potato')
    add('Lunch',f'{label} {style}','Soups',[(p,2,'cup','protein',False,'Soup Protein'),(v,3,'cup','produce',False,'Flexible Vegetables'),(carb,1.5,'cup','starch',False,'Soup Starch'),('stock',6,'cup','liquid',False,'Stock'),('onion',1,'each','produce',True,'Aromatics')],['Soften onion.','Add vegetables, protein and stock.','Simmer until tender.','Thicken if wanted.','Season and serve.'],protein=p,carb=carb,focus=v,freezer=True,onepot=True,veg=p in ['lentils','chickpeas','beans'],swaps='Use canned legumes and frozen vegetables; swap noodles/rice/potato.')

potfills=[('Beans Cheese','baked beans','cheese'),('Tuna Corn','tuna','corn'),('Chicken Broccoli','chicken','broccoli'),('Chickpea Curry','chickpeas','peas'),('Beef Salsa','beef mince','salsa')]
for (label,p,v),fmt in take(potfills,['Baked Potato','Sweet Potato','Potato Bowl','Loaded Potato','Microwave Potato','Crispy Potato'],30):
    base='sweet potato' if fmt=='Sweet Potato' else 'potato'
    add('Lunch',f'{label} {fmt}','Loaded potatoes',[(base,4,'large','starch',False,'Potato'),(p,2,'cup','protein',False,'Lunch Protein'),(v,1.5,'cup','produce/sauce',False,'Flexible Vegetables'),('cheese or yoghurt',0.5,'cup','topping',True,'Dairy Topping')],['Cook potatoes until tender.','Heat filling.','Open or bowl potato.','Add filling.','Top and serve.'],protein=p,carb=base,focus=v,veg=p in ['baked beans','chickpeas'],swaps='Any leftover curry, mince, beans or vegetables can become the topping.')

salads=[('Tuna Pasta','tuna','pasta','corn'),('Chicken Rice','chicken','rice','cucumber'),('Chickpea Couscous','chickpeas','couscous','tomato'),('Egg Potato','egg','potato','peas'),('Bean Corn','beans','rice','corn')]
for (label,p,carb,v),d in take(salads,['lemon herb','yoghurt','mustard','sweet chilli','vinaigrette','tomato herb'],30):
    add('Lunch',f'{label} Salad with {d.title()} Dressing','Salads & pasta salads',[(p,2,'cup','protein',False,'Lunch Protein'),(carb,3,'cup cooked','grain/starch',False,'Rice/Grain'),(v,2,'cup','produce',False,'Flexible Vegetables'),('mixed salad vegetables',2,'cup','produce',False,'Flexible Vegetables'),(f'{d} dressing',0.5,'cup','sauce',False,'Dressing')],['Cook and cool base if needed.','Prepare protein.','Chop vegetables.','Combine.','Dress before serving.'],protein=p,carb=carb,focus=v,lunchbox=True,veg=p in ['chickpeas','egg','beans'],swaps='Use any leftover grain or pasta; dressing and vegetables can be swapped.')

# ---------- DINNER/TEA 250 ----------
dp=['chicken','beef mince','pork','tofu','lentils','beans','sausages','tuna','chickpeas','egg']
for p,prof in take(dp,['Tomato Herb','Creamy Garlic','BBQ Tomato','Pesto Veg','Mild Chilli'],50):
    add('Dinner/Tea',f'{prof} {p.title()} Pasta','Pasta dinners',[('pasta',500,'g','starch',False,'Pasta'),(p,500,'g','protein',False,'Dinner Protein'),(prof.lower()+' sauce',3,'cup','sauce',False,'Pasta Sauce'),('mixed vegetables',3,'cup','produce',False,'Frozen/Seasonal Vegetables'),('cheese',1,'cup','dairy',True,'Cheese')],['Cook pasta.','Cook protein.','Add vegetables and sauce.','Stir through pasta.','Top and serve.'],protein=p,carb='pasta',focus='mixed vegetables',freezer=True,veg=p in ['tofu','lentils','beans','chickpeas','egg'],swaps='Swap pasta shape, protein and sauce; legumes can stretch or replace meat.')

cprof=[('Mild Coconut','coconut milk','mixed vegetables'),('Tomato','canned tomatoes','peas'),('Pumpkin','pumpkin','spinach'),('Korma-Style','yoghurt','carrot'),('Sweet Potato','sweet potato','peas')]
for p,(label,base,v) in take(dp,cprof,50):
    add('Dinner/Tea',f'{label} {p.title()} Curry','Curries & rice',[('rice',2,'cup dry','grain',False,'Rice/Grain'),(p,500,'g','protein',False,'Dinner Protein'),(base,2,'cup','sauce',False,'Curry Base'),(v,3,'cup','produce',False,'Frozen/Seasonal Vegetables'),('mild curry powder or paste',2,'tbsp','flavour',False,'Herbs/Spices')],['Cook rice.','Cook protein.','Add curry flavouring.','Add base and vegetables.','Simmer and serve.'],protein=p,carb='rice',focus=v,freezer=True,veg=p in ['tofu','lentils','beans','chickpeas','egg'],swaps='Rice can become potato or flatbread; use canned legumes for lower-cost versions.')

sprof=[('Teriyaki','teriyaki sauce','broccoli'),('Sweet Chilli','sweet chilli sauce','capsicum'),('Garlic Soy','soy garlic sauce','green beans'),('Honey Soy','honey soy sauce','carrot'),('Satay','peanut sauce','mixed vegetables')]
for p,(label,sauce,v) in take(dp,sprof,50):
    add('Dinner/Tea',f'{label} {p.title()} Stir-Fry','Stir-fries & noodles',[('noodles',400,'g','starch',False,'Noodles'),(p,500,'g','protein',False,'Dinner Protein'),(v,4,'cup','produce',False,'Frozen/Seasonal Vegetables'),(sauce,0.75,'cup','sauce',False,'Stir-fry Sauce'),('oil',1,'tbsp','fat',False,'Cooking Fat')],['Prepare ingredients.','Cook protein.','Cook vegetables.','Add sauce.','Serve with noodles.'],protein=p,carb='noodles',focus=v,onepot=True,veg=p in ['tofu','lentils','beans','chickpeas','egg'],swaps='Swap noodles for rice; fresh or frozen vegetables work.')

tprof=[('Lemon Herb','lemon herb seasoning','potato','carrot'),('Garlic','garlic seasoning','potato','broccoli'),('BBQ','BBQ seasoning','sweet potato','corn'),('Italian','Italian herbs','potato','zucchini'),('Paprika','mild paprika','sweet potato','capsicum')]
for p,(label,season,starch,v) in take(dp,tprof,50):
    add('Dinner/Tea',f'{label} {p.title()} Tray Bake','Tray bakes',[(p,600,'g','protein',False,'Dinner Protein'),(starch,800,'g','starch',False,'Potato'),(v,4,'cup','produce',False,'Frozen/Seasonal Vegetables'),(season,2,'tbsp','flavour',False,'Herbs/Spices'),('oil',2,'tbsp','fat',False,'Cooking Fat')],['Heat oven to 200°C.','Arrange ingredients on tray.','Coat with oil and seasoning.','Roast until cooked.','Serve.'],protein=p,carb=starch,focus=v,onepot=True,veg=p in ['tofu','lentils','beans','chickpeas','egg'],swaps='Use whichever vegetables are cheapest; potato and sweet potato are interchangeable.')

bprof=[('Potato-Topped','potato'),('Pasta Bake','pasta'),('Rice Bake','rice'),('Vegetable Bake','mixed vegetables'),('Breadcrumb Bake','breadcrumbs')]
for p,(label,carb) in take(dp,bprof,50):
    add('Dinner/Tea',f'{p.title()} {label}','Casseroles & bakes',[(p,500,'g','protein',False,'Dinner Protein'),(carb,3,'cup','starch',False,'Bake Base'),('mixed vegetables',3,'cup','produce',False,'Frozen/Seasonal Vegetables'),('simple white or tomato sauce',2,'cup','sauce',False,'Bake Sauce'),('cheese or breadcrumbs',1,'cup','topping',True,'Bake Topping')],['Heat oven to 190°C.','Cook protein and vegetables.','Prepare base if needed.','Combine with sauce.','Top and bake until golden.'],protein=p,carb=carb,focus='mixed vegetables',freezer=True,veg=p in ['tofu','lentils','beans','chickpeas','egg'],swaps='Top the same filling with potato, pasta, rice or crumbs; ideal for leftovers.')

# ---------- SNACKS 100 ----------
sf=['banana','apple','blueberry','carrot','pumpkin','corn','cheese','spinach','sultana','choc chip']
for x,fmt in take(sf,['Mini Muffins','Snack Slice','Oat Cups'],25):
    add('Snack',f'{x.title()} {fmt}','Snack baking',[('self-raising flour or oats',2,'cup','flour/grain',False,'Flour/Oats'),('milk',1,'cup','liquid',False,'Milk'),('eggs',2,'each','protein',False,'Egg'),(x,1.5,'cup','add-in',False,'Fruit/Add-in'),('oil',0.33,'cup','fat',False,'Cooking Fat')],['Heat oven.','Mix dry.','Mix wet.','Combine and add flavour.','Bake until set.'],protein='eggs',carb='flour/oats',focus=x,freezer=True,lunchbox=True,veg=True,swaps='Switch fruit, vegetables, cheese or small sweet add-ins; freeze in portions.')

fp=[('apple','peanut butter'),('banana','yoghurt'),('pear','cheese'),('orange','yoghurt'),('grapes','cheese'),('berries','yoghurt'),('peach','cottage cheese'),('pineapple','yoghurt'),('melon','cheese'),('mango','yoghurt')]
for (fruit,partner),fmt in take(fp,['Snack Cup','Lunchbox Box','Picnic Box'],25):
    add('Snack',f'{fruit.title()} & {partner.title()} {fmt}','Fruit snacks',[(fruit,4,'serve','fruit',False,'Seasonal Fruit'),(partner,1,'cup','protein/topping',False,'Snack Protein'),('crackers or oats',1,'cup','grain',True,'Crackers/Oats')],['Prepare fruit.','Portion partner.','Add grain if wanted.','Divide into containers.','Chill if needed.'],protein=partner,carb='crackers/oats',focus=fruit,lunchbox=True,veg=True,swaps='Use cheapest seasonal fruit; swap dairy for plant alternatives.')

bf=['oat honey','banana oat','apple cinnamon','peanut oat','sultana oat','cocoa oat','seed oat','coconut oat','berry oat','apricot oat']
for x,fmt in take(bf,['No-Bake Bars','Baked Bars','Bites'],25):
    add('Snack',f'{x.title()} {fmt}','Bars & bites',[('rolled oats',3,'cup','grain',False,'Oats/Breakfast Grain'),('honey or syrup',0.5,'cup','sweetener',False,'Sweetener/Flavour'),('peanut or seed butter',0.5,'cup','binder',False,'Nut/Seed Butter'),(x,1,'cup','add-in',False,'Fruit/Add-in')],['Combine base ingredients.','Add flavour.','Press or shape.','Bake if required or chill.','Portion and store.'],carb='oats',freezer=True,lunchbox=True,veg=True,swaps='Use nut-free seed butter for school-safe versions; dried fruit, seeds and cocoa can swap.')

sv=[('cheese','corn'),('hummus','carrot'),('egg','crackers'),('tuna','cucumber'),('beans','salsa'),('popcorn','herbs'),('yoghurt','cucumber'),('cheese','tomato'),('chickpeas','paprika'),('cheese','wraps')]
for (main,side),fmt in take(sv,['Snack Plate','Lunchbox Portion','After-School Snack'],25):
    add('Snack',f'{main.title()} & {side.title()} {fmt}','Savoury snacks',[(main,2,'cup','main',False,'Snack Protein'),(side,2,'cup','side',False,'Snack Side'),('vegetable sticks or fruit',2,'cup','produce',True,'Flexible Vegetables')],['Prepare main.','Prepare side.','Add produce.','Portion.','Serve or pack.'],protein=main,focus=side,lunchbox=True,veg=main!='tuna',swaps='Mix any snack protein with any fruit, vegetable or cracker base.')

# ---------- DESSERT 120 ----------
df=['apple','pear','peach','berry','plum','banana','pineapple','mango','apricot','mixed fruit']
for fruit,fmt in take(df,['Oat Crumble','Cinnamon Crumble','Budget Crumble'],30):
    add('Dessert',f'{fruit.title()} {fmt}','Fruit crumbles',[(fruit,5,'cup','fruit',False,'Seasonal Fruit'),('rolled oats',1.5,'cup','grain',False,'Oats/Breakfast Grain'),('plain flour',1,'cup','flour',False,'Flour'),('brown sugar',0.5,'cup','sweetener',False,'Sweetener/Flavour'),('butter or plant spread',100,'g','fat',False,'Cooking Fat')],['Heat oven.','Place fruit in dish.','Mix topping.','Scatter over fruit.','Bake until bubbling.'],carb='oats/flour',focus=fruit,freezer=True,veg=True,swaps='Fresh, frozen or canned-drained fruit all work; use GF flour/oats and plant spread if needed.')

pf=['chocolate','vanilla','banana','apple cinnamon','lemon','caramel','berry','coconut','coffee','orange']
for x,fmt in take(pf,['Self-Saucing Pudding','Baked Pudding','Family Pudding'],30):
    add('Dessert',f'{x.title()} {fmt}','Puddings',[('self-raising flour',1.5,'cup','flour',False,'Flour'),('milk',1,'cup','liquid',False,'Milk'),('sugar',0.75,'cup','sweetener',False,'Sweetener/Flavour'),('egg',1,'each','protein',False,'Egg'),(x,0.75,'cup','flavour',False,'Dessert Flavour'),('butter or oil',60,'g','fat',False,'Cooking Fat')],['Heat oven.','Mix dry.','Add wet.','Add flavour.','Bake until set.'],carb='flour',focus=x,veg=True,swaps='Keep the same pudding base and swap flavour; plant milk/spread and GF flour can adapt it.')

slf=['chocolate','caramel','lemon','coconut','oat jam','peanut','banana','berry','apple','vanilla']
for x,fmt in take(slf,['Budget Slice','Brownie-Style Slice','Lunchbox Slice'],30):
    add('Dessert',f'{x.title()} {fmt}','Slices & brownies',[('plain flour',2,'cup','flour',False,'Flour'),('sugar',1,'cup','sweetener',False,'Sweetener/Flavour'),('eggs',2,'each','protein',False,'Egg'),('oil or melted butter',0.5,'cup','fat',False,'Cooking Fat'),(x,1,'cup','flavour',False,'Dessert Flavour')],['Heat oven.','Mix base.','Add flavour.','Spread into tin.','Bake, cool and slice.'],carb='flour',freezer=True,lunchbox=True,veg=True,swaps='Keep base and change flavour; cut smaller portions for lunchboxes.')

cf=['banana','apple','carrot','chocolate','vanilla','lemon','orange','berry','pear','coconut']
for x,fmt in take(cf,['Simple Cake','Cupcakes','Mini Cakes'],30):
    add('Dessert',f'{x.title()} {fmt}','Cakes & cupcakes',[('self-raising flour',2,'cup','flour',False,'Flour'),('sugar',0.75,'cup','sweetener',False,'Sweetener/Flavour'),('eggs',2,'each','protein',False,'Egg'),('milk',1,'cup','liquid',False,'Milk'),('oil',0.5,'cup','fat',False,'Cooking Fat'),(x,1,'cup','flavour',False,'Dessert Flavour')],['Heat oven.','Mix dry.','Mix wet.','Combine and add flavour.','Bake until cooked.'],carb='flour',focus=x,freezer=True,veg=True,swaps='One base becomes many flavours; frosting is optional to reduce cost.')

# ---------- BAKING/SIDES 30 ----------
for x,fmt in take(['plain','cheese','herb','corn','pumpkin'],['Scones','Quick Bread','Flatbreads'],15):
    add('Baking/Side',f'{x.title()} {fmt}','Breads & scones',[('self-raising flour',3,'cup','flour',False,'Flour'),('milk or water',1.25,'cup','liquid',False,'Milk/Water'),('oil or butter',0.25,'cup','fat',False,'Cooking Fat'),(x,0.75,'cup','add-in',True,'Savoury Add-in')],['Prepare dough.','Add flavour.','Shape.','Bake or pan-cook.','Serve.'],carb='flour',freezer=True,veg=True,swaps='Keep plain or add cheese, herbs, corn or pumpkin; GF flour and plant milk/spread can be used.')

for v,fmt in take(['potato','sweet potato','carrot','pumpkin','broccoli'],['Roasted','Mash','Seasoned Tray'],15):
    add('Baking/Side',f'{fmt} {v.title()} Side','Vegetable sides',[(v,1,'kg','produce',False,'Flexible Vegetables'),('oil or butter',2,'tbsp','fat',False,'Cooking Fat'),('herbs or seasoning',2,'tsp','flavour',True,'Herbs/Spices')],['Prepare vegetable.','Cook until tender.','Add fat.','Season.','Serve.'],carb=v if 'potato' in v else '',focus=v,onepot=True,veg=True,swaps='Use the cheapest in-season vegetable and change the cooking style.')

assert len(recipes)==800, len(recipes)

swap_headers=['Swap Group','Option 1','Option 2','Option 3','Option 4','Option 5','Option 6','Option 7','Option 8','Option 9']
swaps=[
['Dinner Protein','Chicken','Beef mince','Pork','Tofu','Lentils','Beans','Chickpeas','Eggs','Sausages'],
['Lunch Protein','Chicken','Tuna','Egg','Cheese','Hummus','Chickpeas','Beans','Lentils','Leftover roast'],
['Rice/Grain','Rice','Couscous','Quinoa','Pasta','Potato','Noodles','Pearl barley','Leftover grains','Cauliflower rice'],
['Pasta','Regular pasta','Wholemeal pasta','GF pasta','Lentil pasta','Chickpea pasta','Short pasta','Spaghetti','',''],
['Noodles','Egg noodles','Rice noodles','GF noodles','Spaghetti','Rice','','','',''],
['Wrap/Bread','Wraps','Bread','Pita','Bread rolls','English muffins','GF wraps','GF bread','',''],
['Potato','Potato','Sweet potato','Pumpkin','Rice','Pasta','','','',''],
['Flexible Vegetables','Fresh seasonal','Frozen mixed','Corn','Peas','Carrot','Zucchini','Broccoli','Capsicum','Cabbage'],
['Frozen/Seasonal Vegetables','Frozen mixed','Fresh seasonal','Broccoli','Peas','Corn','Carrot','Green beans','Capsicum','Zucchini'],
['Seasonal Fruit','Banana','Apple','Pear','Frozen berries','Peach','Mango','Pineapple','Canned fruit in juice','Sultanas'],
['Milk','Dairy milk','Soy milk','Oat milk','Almond milk','Lactose-free milk','Coconut drink','','',''],
['Cheese','Cheddar','Mozzarella','Reduced-fat cheese','Dairy-free cheese','Nutritional yeast','','','',''],
['Cooking Fat','Olive oil','Vegetable oil','Canola oil','Butter','Plant spread','','','',''],
['Flour','Plain flour','Wholemeal flour','Self-raising flour','GF flour blend','Oat flour','','','',''],
['Oats/Breakfast Grain','Rolled oats','Quick oats','Certified GF oats','Muesli base','','','','',''],
['Sauce','Tomato','Salsa','BBQ','Sweet chilli','Yoghurt dressing','Pesto','Curry','Teriyaki',''],
['Herbs/Spices','Italian herbs','Paprika','Curry powder','Cinnamon','Garlic','Mixed herbs','Cumin','Lemon pepper',''],
['Sweetener/Flavour','Honey','Maple-style syrup','Brown sugar','White sugar','Vanilla','Cinnamon','','',''],
['Nut/Seed Butter','Peanut butter','Sunflower seed butter','Tahini','Almond butter','Soy nut butter','','','',''],
['Crackers/Oats','Crackers','Rice cakes','Oatcakes','Rolled oats','Toast fingers','GF crackers','','','']]

wb=Workbook.create()
s0=wb.worksheets.add('START HERE'); s1=wb.worksheets.add('Recipes'); s2=wb.worksheets.add('Ingredients'); s3=wb.worksheets.add('Swap Matrix'); s4=wb.worksheets.add('Scaling Rules'); s5=wb.worksheets.add('App Schema')

s0.get_range('A1:H1').merge(); s0.get_range('A1').values=[['GENEVIEVE Family Budget Cookbook™ — Recipe Bank V1']]
s0.get_range('A2:H2').merge(); s0.get_range('A2').values=[['800 scalable, mix-and-change recipes designed for the household recipe engine']]
counts={c:sum(r[1]==c for r in recipes) for c in ['Breakfast','Lunch','Dinner/Tea','Snack','Dessert','Baking/Side']}
s0.get_range('A4:B11').values=[['Metric','Count'],['Total recipes',800],['Breakfast',counts['Breakfast']],['Lunch',counts['Lunch']],['Dinner/Tea',counts['Dinner/Tea']],['Snack',counts['Snack']],['Dessert',counts['Dessert']],['Baking/Side',counts['Baking/Side']]]
s0.get_range('D4:H12').values=[['BUILD PRINCIPLE','','','',''],['Base recipe + quantity table + swap groups + scale rules','','','',''],['One recipe can become many household-specific versions without duplicating the full recipe.','','','',''],['','','','',''],['APP SECTIONS','','','',''],['Breakfast','Lunch','Dinner/Tea','Snack','Dessert'],['Budget meals','Lunchbox','Freezer','Vegetarian','One-pot'],['GF adaptable','DF adaptable','Use leftovers','Frozen/canned','Batch cook'],['Important','Dietary adaptability is a prompt only; users still need to check labels/allergens.','','','']]

rh=['Recipe ID','Meal Type','Recipe Name','Base Family','Base Serves','Prep Min','Cook Min','Budget Tier','Primary Protein','Carb/Base','Produce Focus','Freezer Friendly','Lunchbox Friendly','Vegetarian Base','GF Adaptable','DF Adaptable','One Pan/Pot','Method','Mix & Change Notes']
s1.get_range_by_indexes(0,0,len(recipes)+1,len(rh)).values=[rh]+recipes; s1.freeze_panes.freeze_rows(1)
ih=['Recipe ID','Ingredient #','Ingredient','Base Qty','Unit','Ingredient Group','Optional','Swap Group']
s2.get_range_by_indexes(0,0,len(ingredients)+1,len(ih)).values=[ih]+ingredients; s2.freeze_panes.freeze_rows(1)
s3.get_range_by_indexes(0,0,len(swaps)+1,len(swap_headers)).values=[swap_headers]+swaps; s3.freeze_panes.freeze_rows(1)

s4.get_range('A1:F1').merge(); s4.get_range('A1').values=[['Household Scaling Engine — Core Rules']]
s4.get_range('A3:D12').values=[['Rule','Formula / Behaviour','Example','App Note'],['Universal quantity','Scaled Qty = Base Qty × Target Serves ÷ Base Serves','2 cups at 4 → 3 cups at 6','Default measurable rule'],['Whole eggs','Round to practical whole egg','2 × 1.5 = 3 eggs','No fractional eggs'],['Cans/packs','Keep exact recipe qty; round shopping qty up','1.5 cans → buy 2','Separate cooking from shopping quantity'],['Small measures','Round to practical kitchen fractions','1.33 tbsp → 1⅓ tbsp','Friendly display'],['Salt/pepper','Scale gently then to taste','Do not blindly double','Taste-sensitive'],['Chilli/strong spice','Cap auto scaling and prompt user','1 tsp at 4 → suggest 1.5 at 8','Comfort rule'],['Raising agents','Scale linearly only for household batch range','3 tsp → 4.5 tsp at 1.5×','Large batches need testing'],['Pan oil','Do not fully scale with serves','1 tbsp may still suit 6','Cooking-process quantity'],['Optional topping','Scale suggestion; user override','½ cup → ¾ cup','Budget mode can reduce/remove']]
s4.get_range('A15:D22').values=[['Simple calculator','','',''],['Base quantity',2,'cups',''],['Base serves',4,'people',''],['Target serves',6,'people',''],['Scale factor','','',''],['Scaled quantity','','',''],['','','',''],['Logic','Base Qty × Target ÷ Base','','']]
s4.get_range('B19').formulas=[['=B18/B17']]; s4.get_range('B20').formulas=[['=B16*B19']]

s5.get_range('A1:F1').merge(); s5.get_range('A1').values=[['Developer-ready recipe content schema']]
s5.get_range('A3:F18').values=[['Entity','Field','Type','Required','Purpose','Notes'],['Recipe','recipe_id','text','Yes','Stable identifier','GEN-RCP-####'],['Recipe','meal_type','enum','Yes','Category/navigation',''],['Recipe','recipe_name','text','Yes','Display name',''],['Recipe','base_family','text','Yes','Variant family','Mix/change grouping'],['Recipe','base_serves','integer','Yes','Scaling denominator','Default 4'],['Recipe','dietary_flags','booleans','No','Adaptation prompts','Not an allergen guarantee'],['RecipeIngredient','recipe_id','FK','Yes','Recipe link',''],['RecipeIngredient','ingredient','text','Yes','Display ingredient',''],['RecipeIngredient','base_qty','decimal','Yes','Scale input',''],['RecipeIngredient','unit','text','Yes','Display unit',''],['RecipeIngredient','swap_group','text','No','Substitution engine','Links Swap Matrix'],['UserRecipe','target_serves','integer','Yes','Household size','User controlled'],['UserRecipe','selected_swaps','json','No','Chosen alternatives',''],['Planner','meal_date','date','Yes','Weekly plan',''],['Planner','recipe_id','FK','Yes','Meal selection','']]

# Minimal professional styling (faster export)
title={'fill':'#111111','font':{'bold':True,'color':'#C9A227','size':16},'horizontal_alignment':'center'}
hdr={'fill':'#111111','font':{'bold':True,'color':'#FFFFFF'},'wrap_text':True}
s0.get_range('A1:H1').format=title; s1.get_range('A1:S1').format=hdr; s2.get_range('A1:H1').format=hdr; s3.get_range('A1:J1').format=hdr; s4.get_range('A1:F1').format=title; s4.get_range('A3:D3').format=hdr; s5.get_range('A1:F1').format=title; s5.get_range('A3:F3').format=hdr
s1.get_range(f'A1:S{len(recipes)+1}').format.wrap_text=True; s2.get_range(f'A1:H{len(ingredients)+1}').format.wrap_text=True
for c,w in {'A':14,'B':14,'C':34,'D':24,'E':10,'F':10,'G':10,'H':12,'I':18,'J':18,'K':18,'L':14,'M':14,'N':14,'O':12,'P':12,'Q':12,'R':50,'S':50}.items(): s1.get_range(f'{c}:{c}').format.column_width=w
for c,w in {'A':14,'B':12,'C':30,'D':12,'E':14,'F':18,'G':12,'H':24}.items(): s2.get_range(f'{c}:{c}').format.column_width=w
s0.get_range('A:H').format.column_width=20; s4.get_range('A:D').format.column_width=28; s5.get_range('A:F').format.column_width=22

out='/mnt/data/GENEVIEVE_Family_Budget_Cookbook_Recipe_Bank_V1_800.xlsx'
SpreadsheetFile.export_xlsx(wb).save(out)
print(f'Created {len(recipes)} recipes and {len(ingredients)} normalized ingredient rows.')
print(wb.inspect({'kind':'table','range':'START HERE!A1:H12','include':'values,formulas','table_max_rows':12,'table_max_cols':8}).ndjson[:3000])
print(wb.inspect({'kind':'match','search_term':'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A','options':{'use_regex':True,'max_results':50},'summary':'formula error scan'}).ndjson[:1000])
print(out)
