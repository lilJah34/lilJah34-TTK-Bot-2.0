import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from data_manager import data_manager
from utils import is_admin, generate_product_id, get_current_time
from config import PRODUCT_CATEGORIES, STAR_RATINGS, DEFAULT_PRICES

logger = logging.getLogger(__name__)

async def handle_product_category_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, category: str):
    """Handle product category selection during creation with enhanced UI."""
    user_data = context.user_data
    product_data = user_data.get('product_data', {})
    
    product_data['category'] = category
    
    # Enhanced category confirmation with preview
    text = f"""
📦 **Product Category Selected**

✅ **Category:** {category}
📷 **Media:** {product_data.get('media_type', 'photo').title()} uploaded
📝 **Name:** {product_data.get('name', 'Set')}

🌟 **Select Quality Rating:**
"""
    
    # Create a more visual rating selection
    keyboard = []
    rating_descriptions = {
        '⭐': 'Basic Quality',
        '⭐⭐': 'Good Quality', 
        '⭐⭐⭐': 'Great Quality',
        '⭐⭐⭐⭐': 'Premium Quality',
        '⭐⭐⭐⭐⭐': 'Top Shelf'
    }
    
    for rating in STAR_RATINGS:
        description = rating_descriptions.get(rating, '')
        button_text = f"{rating} {description}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"prodrating_{rating}")])
    
    keyboard.extend([
        [InlineKeyboardButton("🔄 Change Category", callback_data="change_category")],
        [InlineKeyboardButton("❌ Cancel Creation", callback_data="cancel_product_creation")]
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    user_data['product_data'] = product_data

async def handle_product_rating_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, rating: str):
    """Handle star rating selection with enhanced pricing preview."""
    user_data = context.user_data
    product_data = user_data.get('product_data', {})
    
    product_data['grade'] = rating
    category = product_data.get('category')
    
    # Get default prices for this category and rating
    default_prices = DEFAULT_PRICES.get(category, {}).get(rating, {})
    
    if default_prices:
        product_data['prices'] = default_prices.copy()
        
        # Enhanced pricing display with better formatting
        price_display = []
        for size, price in default_prices.items():
            from utils import get_size_display_name
            size_name = get_size_display_name(size)
            price_display.append(f"• {size_name}: **${price}**")
        
        price_text = "\n".join(price_display)
        
        text = f"""
🌟 **Product Setup Complete**

📦 **Product:** {product_data.get('name')}
📂 **Category:** {category}
⭐ **Quality:** {rating}

💰 **Suggested Pricing:**
{price_text}

Choose your pricing approach:
"""
        
        keyboard = [
            [InlineKeyboardButton("✅ Use Suggested Prices", callback_data="prod_use_default_prices")],
            [InlineKeyboardButton("💰 Set Custom Pricing", callback_data="prod_custom_prices")],
            [InlineKeyboardButton("👁️ Preview Product", callback_data="prod_preview")],
            [InlineKeyboardButton("🔙 Change Rating", callback_data="change_rating")],
            [InlineKeyboardButton("❌ Cancel Creation", callback_data="cancel_product_creation")]
        ]
        
    else:
        # No default prices, must set custom with helpful guidance
        text = f"""
🌟 **Product Setup**

📦 **Product:** {product_data.get('name')}
📂 **Category:** {category}
⭐ **Quality:** {rating}

💰 **Custom Pricing Required**
This category/rating combination requires custom pricing.

Set competitive prices based on your market research.
"""
        
        keyboard = [
            [InlineKeyboardButton("💰 Set Custom Pricing", callback_data="prod_custom_prices")],
            [InlineKeyboardButton("📊 View Market Rates", callback_data="prod_market_rates")],
            [InlineKeyboardButton("🔙 Change Rating", callback_data="change_rating")],
            [InlineKeyboardButton("❌ Cancel Creation", callback_data="cancel_product_creation")]
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    user_data['product_data'] = product_data

async def handle_use_default_prices(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle using default prices for product."""
    user_data = context.user_data
    product_data = user_data.get('product_data', {})
    
    # Finalize product with default prices
    from handlers.message_handlers import finalize_product_creation
    await finalize_product_creation(update, context, product_data)

async def handle_custom_prices_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle request for custom pricing with enhanced UI guidance."""
    user_data = context.user_data
    product_data = user_data.get('product_data', {})
    category = product_data.get('category')
    grade = product_data.get('grade', '⭐⭐⭐')
    
    # Enhanced pricing guidance with visual examples
    size_info = {
        '🌿 Flower': {
            'sizes': ['eighth', 'quarter', 'half', 'oz'],
            'example': 'eighth:30,quarter:55,half:105,oz:200',
            'description': '⅛, ¼, ½, and full ounce options'
        },
        '🍯 Concentrates': {
            'sizes': ['gram'],
            'example': 'gram:40',
            'description': 'Per gram pricing'
        },
        '🍫 Edibles': {
            'sizes': ['unit'],
            'example': 'unit:20',
            'description': 'Per piece/package pricing'
        },
        '🚬 Pre-Rolls': {
            'sizes': ['single', 'pack_5'],
            'example': 'single:12,pack_5:55',
            'description': 'Individual or 5-pack options'
        }
    }
    
    category_info = size_info.get(category, {
        'sizes': ['unit'],
        'example': 'unit:25',
        'description': 'Standard unit pricing'
    })
    
    # Show competitive pricing suggestions
    suggested_ranges = {
        '⭐': 'Budget-friendly pricing',
        '⭐⭐': 'Value pricing',
        '⭐⭐⭐': 'Market rate pricing',
        '⭐⭐⭐⭐': 'Premium pricing',
        '⭐⭐⭐⭐⭐': 'Top-shelf pricing'
    }
    
    pricing_hint = suggested_ranges.get(grade, 'Competitive pricing')
    
    text = f"""
💰 **Custom Pricing Setup**

📦 **Product:** {product_data.get('name')}
📂 **Category:** {category}
⭐ **Quality:** {grade} ({pricing_hint})

📏 **Available Sizes:**
{category_info['description']}

📝 **Format Instructions:**
Enter prices as: `size:price,size:price`

**Example for {category}:**
`{category_info['example']}`

💡 **Quick Tips:**
• Use whole numbers (no decimals)
• Separate sizes with commas
• No spaces around colons
• Round to nearest $5 for flower

**Send your pricing now:**
"""
    
    keyboard = [
        [InlineKeyboardButton("📋 Copy Example", callback_data=f"copy_example_{category}")],
        [InlineKeyboardButton("📊 Market Research", callback_data="prod_market_rates")],
        [InlineKeyboardButton("🔙 Use Suggested Prices", callback_data="prod_use_default_prices")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_product_creation")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    # Set flag to expect price input
    user_data['awaiting_price_override'] = True

async def cancel_product_creation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel product creation process."""
    # Clear user state
    context.user_data.clear()
    
    await update.callback_query.edit_message_text(
        "❌ Product creation cancelled.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Back to Admin", callback_data="admin")]
        ])
    )

# Callback handlers for product creation workflow
async def handle_product_creation_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle product creation related callbacks."""
    
    if data.startswith("prodcat_"):
        category = data.replace("prodcat_", "")
        await handle_product_category_selection(update, context, category)
    
    elif data.startswith("prodrating_"):
        rating = data.replace("prodrating_", "")
        await handle_product_rating_selection(update, context, rating)
    
    elif data == "prod_use_default_prices":
        await handle_use_default_prices(update, context)
    
    elif data == "prod_custom_prices":
        await handle_custom_prices_request(update, context)
    
    elif data == "cancel_product_creation":
        await cancel_product_creation(update, context)
    
    elif data == "admin_add_another":
        # Start new product creation
        context.user_data.clear()
        context.user_data['creating_product'] = True
        context.user_data['product_data'] = {}
        
        await update.callback_query.edit_message_text(
            "📷 **Add New Product**\n\nPlease send a photo or video of the product to get started."
        )

async def handle_product_visibility_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle toggling product visibility."""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.callback_query.answer("❌ Access denied.")
        return
    
    # Parse data: "toggle_visibility_category_productid"
    parts = data.split("_", 3)
    if len(parts) != 4:
        await update.callback_query.answer("❌ Invalid action.")
        return
    
    category = parts[2]
    product_id = parts[3]
    
    product = data_manager.get_product(category, product_id)
    if not product:
        await update.callback_query.answer("❌ Product not found.")
        return
    
    # Toggle visibility
    current_visibility = product.get('visible', True)
    new_visibility = not current_visibility
    
    data_manager.update_product_visibility(category, product_id, new_visibility)
    
    status = "visible" if new_visibility else "hidden"
    await update.callback_query.answer(f"✅ Product is now {status}")
    
    logger.info(f"Admin {user_id} toggled product {product_id} visibility to {new_visibility}")

async def handle_product_editing(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle product editing requests."""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.callback_query.answer("❌ Access denied.")
        return
    
    # This would handle editing existing products
    # Implementation would be similar to creation but pre-fill existing data
    await update.callback_query.edit_message_text(
        "✏️ **Product Editing**\n\nProduct editing features coming soon!",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Back to Admin", callback_data="admin")]
        ])
    )
