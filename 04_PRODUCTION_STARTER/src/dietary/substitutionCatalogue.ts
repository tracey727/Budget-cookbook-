/**
 * Phase 2.5 -- Substitution catalogue.
 *
 * SWAP_GROUPS is the V1 prototype's own swap data (03_WORKING_PROTOTYPE/data.js
 * `swapMap`) -- the "function" a substitution must be mapped to per
 * DIETARY_REQUIREMENTS_MASTER_BLUEPRINT.md's substitution rule ("it is mapped
 * to the ingredient function needed by the recipe"). It is not re-invented
 * here; this file only adds the dietary-attribute layer swap options never
 * had.
 *
 * Most substitute option names (e.g. "Chicken", "Rice", "Cheese") are the
 * same generic ingredient already classified in
 * 07_DIETARY_REQUIREMENTS_ENGINE/ingredient_dietary_attributes_v1.json --
 * INGREDIENT_KEY_ALIASES maps the display name to that table's key so this
 * file doesn't re-derive facts Phase 2.2 already reviewed. SUBSTITUTE_ONLY_ATTRIBUTES
 * covers the ~60 names that are genuinely new (mostly the free-from products
 * that make adaptation possible at all: GF flour/pasta/bread, plant milks,
 * nut-free butters, Certified GF oats).
 */
import type { AttributeRow, AttributeLookup } from "./substitution";

function a(
  attribute_code: string,
  attribute_value: string,
  evidence_state: AttributeRow["evidence_state"],
  notes?: string,
): AttributeRow {
  return { attribute_code, attribute_value, evidence_state, notes };
}

export const SWAP_GROUPS: Record<string, string[]> = {
  "Dinner Protein": ["Chicken", "Beef mince", "Pork", "Tofu", "Lentils", "Beans", "Chickpeas", "Eggs", "Sausages"],
  "Lunch Protein": ["Chicken", "Tuna", "Egg", "Cheese", "Hummus", "Chickpeas", "Beans", "Lentils", "Leftover roast"],
  "Rice/Grain": ["Rice", "Couscous", "Quinoa", "Pasta", "Potato", "Noodles", "Pearl barley", "Leftover grains", "Cauliflower rice"],
  "Pasta": ["Regular pasta", "Wholemeal pasta", "GF pasta", "Lentil pasta", "Chickpea pasta", "Short pasta", "Spaghetti"],
  "Noodles": ["Egg noodles", "Rice noodles", "GF noodles", "Spaghetti", "Rice"],
  "Wrap/Bread": ["Wraps", "Bread", "Pita", "Bread rolls", "English muffins", "GF wraps", "GF bread"],
  "Potato": ["Potato", "Sweet potato", "Pumpkin", "Rice", "Pasta"],
  "Flexible Vegetables": ["Fresh seasonal", "Frozen mixed", "Corn", "Peas", "Carrot", "Zucchini", "Broccoli", "Capsicum", "Cabbage"],
  "Frozen/Seasonal Vegetables": ["Frozen mixed", "Fresh seasonal", "Broccoli", "Peas", "Corn", "Carrot", "Green beans", "Capsicum", "Zucchini"],
  "Seasonal Fruit": ["Banana", "Apple", "Pear", "Frozen berries", "Peach", "Mango", "Pineapple", "Canned fruit in juice", "Sultanas"],
  "Milk": ["Dairy milk", "Soy milk", "Oat milk", "Almond milk", "Lactose-free milk", "Coconut drink"],
  "Cheese": ["Cheddar", "Mozzarella", "Reduced-fat cheese", "Dairy-free cheese", "Nutritional yeast"],
  "Cooking Fat": ["Olive oil", "Vegetable oil", "Canola oil", "Butter", "Plant spread"],
  "Flour": ["Plain flour", "Wholemeal flour", "Self-raising flour", "GF flour blend", "Oat flour"],
  "Oats/Breakfast Grain": ["Rolled oats", "Quick oats", "Certified GF oats", "Muesli base"],
  "Sauce": ["Tomato", "Salsa", "BBQ", "Sweet chilli", "Yoghurt dressing", "Pesto", "Curry", "Teriyaki"],
  "Herbs/Spices": ["Italian herbs", "Paprika", "Curry powder", "Cinnamon", "Garlic", "Mixed herbs", "Cumin", "Lemon pepper"],
  "Sweetener/Flavour": ["Honey", "Maple-style syrup", "Brown sugar", "White sugar", "Vanilla", "Cinnamon"],
  "Nut/Seed Butter": ["Peanut butter", "Sunflower seed butter", "Tahini", "Almond butter", "Soy nut butter"],
  "Crackers/Oats": ["Crackers", "Rice cakes", "Oatcakes", "Rolled oats", "Toast fingers", "GF crackers"],
};

/** Display name (as it appears in SWAP_GROUPS) -> key in
 * ingredient_dietary_attributes_v1.json, for options that are the same
 * generic ingredient Phase 2.2 already classified. */
export const INGREDIENT_KEY_ALIASES: Record<string, string> = {
  "Apple": "apple", "Banana": "banana", "Beans": "beans", "Beef mince": "beef mince",
  "Bread": "bread", "Bread rolls": "bread rolls", "Broccoli": "broccoli", "Brown sugar": "brown sugar",
  "Cabbage": "cabbage", "Capsicum": "capsicum", "Carrot": "carrot", "Cheese": "cheese",
  "Chicken": "chicken", "Chickpeas": "chickpeas", "Cinnamon": "cinnamon", "Corn": "corn",
  "Couscous": "couscous", "Crackers": "crackers", "Egg": "egg", "Eggs": "eggs",
  "English muffins": "english muffins", "Green beans": "green beans", "Honey": "honey",
  "Hummus": "hummus", "Italian herbs": "italian herbs", "Lentils": "lentils", "Mango": "mango",
  "Noodles": "noodles", "Oat flour": "oat flour", "Paprika": "paprika", "Pasta": "pasta",
  "Peach": "peach", "Peanut butter": "peanut butter", "Pear": "pear", "Peas": "peas",
  "Pineapple": "pineapple", "Plain flour": "plain flour",
  "Pork": "pork", "Potato": "potato", "Pumpkin": "pumpkin", "Rice": "rice",
  "Rolled oats": "rolled oats", "Salsa": "salsa", "Sausages": "sausages",
  "Self-raising flour": "self-raising flour", "Sultanas": "sultana", "Sweet potato": "sweet potato",
  "Tofu": "tofu", "Tomato": "tomato", "Tuna": "tuna", "Vanilla": "vanilla",
  "Wholemeal flour": "wholemeal flour", "Wraps": "wraps", "Yoghurt dressing": "yoghurt dressing",
  "Zucchini": "zucchini",
  "Leftover roast": "leftover roast meat", "Pita": "pita bread", "BBQ": "bbq sauce",
  "Curry": "mild curry sauce", "Teriyaki": "teriyaki sauce", "Pesto": "pesto veg sauce",
  "Sweet chilli": "sweet chilli sauce", "Dairy milk": "milk",
  "Olive oil": "oil", "Canola oil": "oil", "Vegetable oil": "oil",
};

/** Genuinely new substitute-specific products/items not in the main
 * ingredient table -- mostly the free-from options that make adaptation
 * possible (GF/plant-based/nut-free alternatives), reviewed the same way
 * Phase 2.2 reviewed the base ingredient list: real facts get VERIFIED_*,
 * anything brand/product-dependent gets CONDITIONAL with a note. */
export const SUBSTITUTE_ONLY_ATTRIBUTES: AttributeLookup = {
  // "Butter" and "Plant spread" are NOT top-level entries in
  // ingredient_dietary_attributes_v1.json -- they only exist as internal
  // sub-terms in build_ingredient_dietary_attributes.py used to decompose
  // "X or Y" compound lines like "butter or oil" (found while wiring up
  // this alias table: the alias check below caught both as missing keys).
  // Restated here directly rather than aliased, matching that script's own
  // EXACT_RULES values for these terms exactly.
  "Butter": [a("ANIMAL_DERIVED", "true", "VERIFIED_PRESENT"), a("DAIRY_MILK", "true", "VERIFIED_PRESENT"),
    a("LACTOSE_CONTENT", "true", "VERIFIED_PRESENT"), a("ALLERGEN_MILK", "true", "VERIFIED_PRESENT")],
  "Plant spread": [a("ANIMAL_DERIVED", "unspecified", "CONDITIONAL", "Some margarine/plant-spread blends contain buttermilk or milk solids; verify product."),
    a("DAIRY_MILK", "unspecified", "CONDITIONAL", "Some margarine/plant-spread blends contain buttermilk or milk solids; verify product.")],
  "Almond butter": [a("ANIMAL_DERIVED", "false", "VERIFIED_ABSENT"), a("ALLERGEN_ALMOND", "true", "VERIFIED_PRESENT")],
  "Almond milk": [a("ANIMAL_DERIVED", "false", "VERIFIED_ABSENT"), a("DAIRY_MILK", "false", "VERIFIED_ABSENT"),
    a("LACTOSE_CONTENT", "false", "VERIFIED_ABSENT"), a("ALLERGEN_MILK", "false", "VERIFIED_ABSENT"),
    a("ALLERGEN_ALMOND", "true", "VERIFIED_PRESENT")],
  "Canned fruit in juice": [a("ANIMAL_DERIVED", "false", "VERIFIED_ABSENT")],
  "Cauliflower rice": [a("ANIMAL_DERIVED", "false", "VERIFIED_ABSENT"), a("ALLERGEN_WHEAT", "false", "VERIFIED_ABSENT")],
  "Certified GF oats": [a("ANIMAL_DERIVED", "false", "VERIFIED_ABSENT"), a("ALLERGEN_OATS", "true", "VERIFIED_PRESENT"),
    a("OAT_GF_CERTIFIED", "true", "VERIFIED_PRESENT",
      "The specific verified gluten-free-certified oat product the AU claim boundary requires -- see REFERENCE_SOURCES.md. Still contains oats (relevant to an oat allergy), but resolves the coeliac/gluten-free uncertainty plain oats carry.")],
  "Cheddar": [a("ANIMAL_DERIVED", "true", "VERIFIED_PRESENT"), a("DAIRY_MILK", "true", "VERIFIED_PRESENT"),
    a("LACTOSE_CONTENT", "true", "VERIFIED_PRESENT"), a("ALLERGEN_MILK", "true", "VERIFIED_PRESENT")],
  "Chickpea pasta": [a("ANIMAL_DERIVED", "false", "VERIFIED_ABSENT"), a("ALLERGEN_WHEAT", "false", "VERIFIED_ABSENT")],
  "Coconut drink": [a("ANIMAL_DERIVED", "false", "VERIFIED_ABSENT"), a("DAIRY_MILK", "false", "VERIFIED_ABSENT"),
    a("LACTOSE_CONTENT", "false", "VERIFIED_ABSENT"), a("ALLERGEN_MILK", "false", "VERIFIED_ABSENT")],
  "Dairy-free cheese": [a("ANIMAL_DERIVED", "false", "VERIFIED_ABSENT"), a("DAIRY_MILK", "false", "VERIFIED_ABSENT"),
    a("LACTOSE_CONTENT", "false", "VERIFIED_ABSENT"), a("ALLERGEN_MILK", "false", "VERIFIED_ABSENT"),
    a("ALLERGEN_CASHEW", "unspecified", "CONDITIONAL", "Many dairy-free cheeses are cashew- or other nut-based; not implied by the name -- verify product for a tree-nut allergy."),
    a("ALLERGEN_SOY", "unspecified", "CONDITIONAL", "Some dairy-free cheeses use soy protein; verify product.")],
  "Egg noodles": [a("ANIMAL_DERIVED", "true", "VERIFIED_PRESENT"), a("EGG", "true", "VERIFIED_PRESENT"),
    a("ALLERGEN_EGG", "true", "VERIFIED_PRESENT"), a("ALLERGEN_WHEAT", "true", "VERIFIED_PRESENT")],
  "Fresh seasonal": [a("ANIMAL_DERIVED", "false", "VERIFIED_ABSENT")],
  "Frozen berries": [a("ANIMAL_DERIVED", "false", "VERIFIED_ABSENT")],
  "Frozen mixed": [a("ANIMAL_DERIVED", "false", "VERIFIED_ABSENT")],
  "Garlic": [a("ANIMAL_DERIVED", "false", "VERIFIED_ABSENT"), a("GARLIC_CONTENT", "true", "VERIFIED_PRESENT")],
  "GF bread": [a("ANIMAL_DERIVED", "false", "VERIFIED_ABSENT"), a("ALLERGEN_WHEAT", "false", "VERIFIED_ABSENT")],
  "GF crackers": [a("ANIMAL_DERIVED", "false", "VERIFIED_ABSENT"), a("ALLERGEN_WHEAT", "false", "VERIFIED_ABSENT")],
  "GF flour blend": [a("ANIMAL_DERIVED", "false", "VERIFIED_ABSENT"), a("ALLERGEN_WHEAT", "false", "VERIFIED_ABSENT")],
  "GF noodles": [a("ANIMAL_DERIVED", "false", "VERIFIED_ABSENT"), a("ALLERGEN_WHEAT", "false", "VERIFIED_ABSENT")],
  "GF pasta": [a("ANIMAL_DERIVED", "false", "VERIFIED_ABSENT"), a("ALLERGEN_WHEAT", "false", "VERIFIED_ABSENT")],
  "GF wraps": [a("ANIMAL_DERIVED", "false", "VERIFIED_ABSENT"), a("ALLERGEN_WHEAT", "false", "VERIFIED_ABSENT")],
  "Lactose-free milk": [a("ANIMAL_DERIVED", "true", "VERIFIED_PRESENT"), a("DAIRY_MILK", "true", "VERIFIED_PRESENT"),
    a("ALLERGEN_MILK", "true", "VERIFIED_PRESENT"),
    a("LACTOSE_CONTENT", "false", "VERIFIED_ABSENT", "Still dairy and still carries the milk allergen -- only the lactose sugar is removed. Satisfies LACTOSE_FREE, not DAIRY_FREE or a milk allergy.")],
  "Leftover grains": [a("ANIMAL_DERIVED", "false", "VERIFIED_ABSENT"),
    a("ALLERGEN_WHEAT", "unspecified", "CONDITIONAL", "Grain type not specified (could be couscous/wheat-based or rice/gluten-free); verify before relying on this for a wheat/coeliac requirement.")],
  "Lemon pepper": [a("ANIMAL_DERIVED", "false", "VERIFIED_ABSENT")],
  "Lentil pasta": [a("ANIMAL_DERIVED", "false", "VERIFIED_ABSENT"), a("ALLERGEN_WHEAT", "false", "VERIFIED_ABSENT")],
  "Maple-style syrup": [a("ANIMAL_DERIVED", "false", "VERIFIED_ABSENT"), a("HONEY_BEE_DERIVED", "false", "VERIFIED_ABSENT")],
  "Mixed herbs": [a("ANIMAL_DERIVED", "false", "VERIFIED_ABSENT")],
  "Mozzarella": [a("ANIMAL_DERIVED", "true", "VERIFIED_PRESENT"), a("DAIRY_MILK", "true", "VERIFIED_PRESENT"),
    a("LACTOSE_CONTENT", "true", "VERIFIED_PRESENT"), a("ALLERGEN_MILK", "true", "VERIFIED_PRESENT")],
  "Muesli base": [a("ANIMAL_DERIVED", "false", "VERIFIED_ABSENT"), a("ALLERGEN_OATS", "true", "CONDITIONAL", "Muesli is typically oat-based but blends vary; verify product."),
    a("GLUTEN_CEREAL_OATS", "true", "CONDITIONAL")],
  "Nutritional yeast": [a("ANIMAL_DERIVED", "false", "VERIFIED_ABSENT"), a("DAIRY_MILK", "false", "VERIFIED_ABSENT")],
  "Oat milk": [a("ANIMAL_DERIVED", "false", "VERIFIED_ABSENT"), a("DAIRY_MILK", "false", "VERIFIED_ABSENT"),
    a("LACTOSE_CONTENT", "false", "VERIFIED_ABSENT"), a("ALLERGEN_MILK", "false", "VERIFIED_ABSENT"),
    a("ALLERGEN_OATS", "true", "VERIFIED_PRESENT"),
    a("GLUTEN_CEREAL_OATS", "true", "VERIFIED_PRESENT", "Still oat-derived -- subject to the same Australian gluten-free oats claim boundary as any other oat product unless the specific product is GF-certified.")],
  "Oatcakes": [a("ANIMAL_DERIVED", "false", "VERIFIED_ABSENT"), a("ALLERGEN_OATS", "true", "VERIFIED_PRESENT"),
    a("GLUTEN_CEREAL_OATS", "true", "VERIFIED_PRESENT")],
  "Pearl barley": [a("ANIMAL_DERIVED", "false", "VERIFIED_ABSENT"), a("ALLERGEN_BARLEY", "true", "VERIFIED_PRESENT"),
    a("GLUTEN_CEREAL_BARLEY", "true", "VERIFIED_PRESENT")],
  "Quick oats": [a("ANIMAL_DERIVED", "false", "VERIFIED_ABSENT"), a("ALLERGEN_OATS", "true", "VERIFIED_PRESENT"),
    a("GLUTEN_CEREAL_OATS", "true", "VERIFIED_PRESENT")],
  "Quinoa": [a("ANIMAL_DERIVED", "false", "VERIFIED_ABSENT"), a("ALLERGEN_WHEAT", "false", "VERIFIED_ABSENT")],
  "Reduced-fat cheese": [a("ANIMAL_DERIVED", "true", "VERIFIED_PRESENT"), a("DAIRY_MILK", "true", "VERIFIED_PRESENT"),
    a("LACTOSE_CONTENT", "true", "VERIFIED_PRESENT"), a("ALLERGEN_MILK", "true", "VERIFIED_PRESENT",
      "Reduced fat is not the same as dairy-free or lactose-free -- still ordinary dairy.")],
  "Regular pasta": [a("ANIMAL_DERIVED", "false", "VERIFIED_ABSENT"), a("ALLERGEN_WHEAT", "true", "VERIFIED_PRESENT")],
  "Rice cakes": [a("ANIMAL_DERIVED", "false", "VERIFIED_ABSENT"),
    a("ALLERGEN_WHEAT", "false", "CONDITIONAL", "Most rice cakes are plain rice, but multigrain/blended varieties containing wheat exist; verify product.")],
  "Rice noodles": [a("ANIMAL_DERIVED", "false", "VERIFIED_ABSENT"),
    a("ALLERGEN_WHEAT", "false", "CONDITIONAL", "Typically rice-based, but some blended rice/wheat noodle products exist; verify product.")],
  "Short pasta": [a("ANIMAL_DERIVED", "false", "VERIFIED_ABSENT"), a("ALLERGEN_WHEAT", "true", "VERIFIED_PRESENT")],
  "Soy milk": [a("ANIMAL_DERIVED", "false", "VERIFIED_ABSENT"), a("DAIRY_MILK", "false", "VERIFIED_ABSENT"),
    a("LACTOSE_CONTENT", "false", "VERIFIED_ABSENT"), a("ALLERGEN_MILK", "false", "VERIFIED_ABSENT"),
    a("ALLERGEN_SOY", "true", "VERIFIED_PRESENT")],
  "Soy nut butter": [a("ANIMAL_DERIVED", "false", "VERIFIED_ABSENT"), a("ALLERGEN_SOY", "true", "VERIFIED_PRESENT"),
    a("ALLERGEN_PEANUT", "false", "VERIFIED_ABSENT", "Marketed specifically as the peanut-free nut/seed-butter alternative.")],
  "Spaghetti": [a("ANIMAL_DERIVED", "false", "VERIFIED_ABSENT"), a("ALLERGEN_WHEAT", "true", "VERIFIED_PRESENT")],
  "Sunflower seed butter": [a("ANIMAL_DERIVED", "false", "VERIFIED_ABSENT"), a("ALLERGEN_PEANUT", "false", "VERIFIED_ABSENT"),
    a("ALLERGEN_SESAME", "false", "VERIFIED_ABSENT"),
    a("ALLERGEN_ALMOND", "false", "VERIFIED_ABSENT", "Marketed specifically as the peanut- and tree-nut-free nut/seed-butter alternative.")],
  "Tahini": [a("ANIMAL_DERIVED", "false", "VERIFIED_ABSENT"), a("ALLERGEN_SESAME", "true", "VERIFIED_PRESENT")],
  "Toast fingers": [a("ANIMAL_DERIVED", "false", "VERIFIED_ABSENT"), a("ALLERGEN_WHEAT", "true", "VERIFIED_PRESENT")],
  "White sugar": [a("ANIMAL_DERIVED", "false", "VERIFIED_ABSENT"), a("HONEY_BEE_DERIVED", "false", "VERIFIED_ABSENT")],
  "Wholemeal pasta": [a("ANIMAL_DERIVED", "false", "VERIFIED_ABSENT"), a("ALLERGEN_WHEAT", "true", "VERIFIED_PRESENT")],
  "Cumin": [a("ANIMAL_DERIVED", "false", "VERIFIED_ABSENT")],
  "Curry powder": [a("ANIMAL_DERIVED", "false", "VERIFIED_ABSENT")],
};
