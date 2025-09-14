import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from data_manager import data_manager
from utils import (
    is_admin, get_current_time, generate_order_id, 
    format_price, round_to_nearest_5, calculate_combo_price,
    calculate_estimated_delivery_time
)
from config import REGIONS, REGION_AREAS, PRODUCT_CATEGORIES, STAR_RATINGS, MUTE_TIMER_OPTIONS, NOTIFICATION_CATEGORIES
from handlers.product_handlers import handle_product_creation_callbacks

logger = logging.getLogger(__name__)

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all callback queries from inline buttons."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    data = query.data
    
    logger.info(f"User {user_id} pressed button: {data}")
    
    try:
        # Region selection
        if data.startswith("select_region_"):
            await handle_region_selection(update, context, data)
        elif data.startswith("confirm_region_"):
            await handle_region_confirmation(update, context, data)
        elif data == "back_to_regions":
            await handle_back_to_regions(update, context)
        
        # Main menu and categories
        elif data == "menu":
            await handle_menu(update, context)
        elif data == "change_region":
            await handle_change_region(update, context)
        elif data.startswith("category_"):
            await handle_category_selection(update, context, data)
        
        # Product actions
        elif data.startswith("product_"):
            await handle_product_action(update, context, data)
        elif data.startswith("add_"):
            await handle_add_to_cart(update, context, data)
        elif data.startswith("view_"):
            await handle_view_product(update, context, data)
        
        # Cart actions
        elif data == "cart":
            await handle_cart(update, context)
        elif data == "clear_cart":
            await handle_clear_cart(update, context)
        elif data == "checkout":
            await handle_checkout(update, context)
        elif data.startswith("remove_cart_") or data.startswith("remove_item_"):
            await handle_remove_from_cart(update, context, data)
        elif data.startswith("decrease_qty_"):
            await handle_decrease_quantity(update, context, data)
        elif data.startswith("increase_qty_"):
            await handle_increase_quantity(update, context, data)
        elif data.startswith("qty_select_"):
            await handle_quantity_selector(update, context, data)
        
        # Order and address management
        elif data.startswith("address_"):
            await handle_address_action(update, context, data)
        elif data == "address_add":
            await handle_address_action(update, context, data)
        elif data == "request_address":
            await handle_address_action(update, context, data)
        elif data.startswith("confirm_order_"):
            await handle_confirm_order(update, context, data)
        elif data.startswith("accept_order_"):
            await handle_accept_order(update, context, data)
        elif data.startswith("reject_order_"):
            await handle_reject_order(update, context, data)
        
        # Admin actions
        elif data == "admin":
            await handle_admin_callback(update, context)
        elif data.startswith("admin_"):
            await handle_admin_action(update, context, data)
        
        # Notification settings
        elif data == "notifications":
            await handle_notifications(update, context)
        elif data == "saved_addresses":
            await handle_saved_addresses(update, context)
        elif data == "mute_settings":
            await handle_mute_settings(update, context)
        elif data == "mute_categories":
            await handle_mute_settings(update, context)
        elif data.startswith("quick_mute_"):
            days = int(data.replace("quick_mute_", ""))
            await handle_quick_mute(update, context, days)
        elif data.startswith("mute_all_"):
            days = int(data.replace("mute_all_", ""))
            await handle_mute_all(update, context, days)
        elif data.startswith("mute_category_"):
            category = data.replace("mute_category_", "")
            await handle_mute_category(update, context, category)
        elif data.startswith("apply_mute_"):
            parts = data.replace("apply_mute_", "").split("_")
            if len(parts) >= 2:
                category = "_".join(parts[:-1])
                days = int(parts[-1])
                await handle_apply_mute(update, context, category, days)
        elif data.startswith("unmute_category_"):
            category = data.replace("unmute_category_", "")
            await handle_unmute_category(update, context, category)
        elif data.startswith("apply_post_order_mute_"):
            days = int(data.replace("apply_post_order_mute_", ""))
            await handle_apply_post_order_mute(update, context, days)
        elif data.startswith("mute_"):
            await handle_mute_action(update, context, data)
        elif data == "unmute_all":
            await handle_unmute_all(update, context)
        elif data == "manage_mutes":
            await handle_manage_mutes(update, context)
        elif data == "post_order_mute":
            await handle_post_order_mute(update, context)
        elif data == "notification_history":
            await handle_notification_history(update, context)
        elif data == "notification_advanced":
            await handle_notification_advanced(update, context)
        elif data.startswith("notify_"):
            category = data.replace("notify_", "")
            await handle_notify_when_available(update, context, category)
        elif data == "setup_more_alerts":
            await handle_setup_more_alerts(update, context)
        elif data.startswith("disable_notify_"):
            category = data.replace("disable_notify_", "")
            await handle_disable_notify(update, context, category)
        
        # Combo and deal actions
        elif data.startswith("combo_"):
            await handle_combo_action(update, context, data)
        
        # Fire sale actions
        elif data.startswith("fire_"):
            await handle_fire_sale_action(update, context, data)
        
        # Additional fire sale actions
        elif data == "fire_start_confirm":
            await handle_fire_sale_start_confirm(update, context)
        elif data == "fire_schedule":
            await handle_fire_sale_schedule(update, context)
        elif data == "fire_targeted":
            await handle_fire_sale_targeted(update, context)
        elif data == "fire_preview":
            await handle_fire_sale_preview(update, context)
        
        # Product creation workflow
        elif (data.startswith("prodcat_") or data.startswith("prodrating_") or 
              data in ["prod_use_default_prices", "prod_custom_prices", "cancel_product_creation", "admin_add_another"]):
            await handle_product_creation_callbacks(update, context, data)
        
        # Notification requests
        elif data.startswith("notify_"):
            await handle_notify_request(update, context, data)
        
        # Region alert actions
        elif data.startswith("alert_region_"):
            await handle_region_alert(update, context, data)
        elif data.startswith("send_alert_"):
            await handle_send_alert(update, context, data)
        elif data == "alert_all_regions":
            await handle_region_broadcast(update, context)
        elif data == "alert_analytics":
            await handle_alert_analytics(update, context)
        elif data == "alert_custom":
            await handle_custom_regional_message(update, context)
        
        # Admin statistics
        elif data == "admin_detailed_stats":
            await handle_admin_statistics(update, context)
        
        # Fire sale toggle
        elif data == "fire_toggle":
            await handle_fire_sale_toggle(update, context)
        elif data == "fire_start_4h":
            await handle_fire_start_duration(update, context, 4)
        elif data == "fire_start_8h":
            await handle_fire_start_duration(update, context, 8)
        elif data == "fire_end_confirm":
            await handle_fire_end(update, context)
        
        # Quantity selection
        elif data.startswith("qty_select_"):
            await handle_quantity_selector(update, context, data)
        elif data.startswith("add_qty_"):
            await handle_add_quantity_to_cart(update, context, data)
        
        else:
            # Handle both text and media messages
            try:
                await query.edit_message_text("❌ Unknown action. Please try again.")
            except:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="❌ Unknown action. Please try again."
                )
    
    except Exception as e:
        logger.error(f"Error handling callback query {data}: {e}")
        # Handle both text and media messages
        try:
            await query.edit_message_text("❌ An error occurred. Please try again.")
        except:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ An error occurred. Please try again."
            )

async def handle_region_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle region selection - show confirmation with sub-areas."""
    user_id = update.effective_user.id
    region_id = data.replace("select_region_", "")
    
    region_name = REGIONS.get(region_id, {}).get('name', region_id)
    sub_areas = REGION_AREAS.get(region_id, [])
    
    # Create confirmation text with sub-areas
    areas_text = "\n".join([f"• {area}" for area in sub_areas])
    
    text = f"""
📍 **Region Confirmation**

You selected: **{region_name}**

Areas covered in this region:
{areas_text}

Is this the correct region for your delivery location?
"""
    
    # Create confirmation keyboard
    keyboard = [
        [InlineKeyboardButton("✅ Yes, Confirm", callback_data=f"confirm_region_{region_id}")],
        [InlineKeyboardButton("🔙 Back to Region Selection", callback_data="back_to_regions")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle menu button press."""
    from handlers.command_handlers import menu
    await menu(update, context)

async def handle_change_region(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle change region button."""
    from handlers.command_handlers import show_region_selection
    await show_region_selection(update, context)

async def handle_category_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle category selection with enhanced browsing interface."""
    category = data.replace("category_", "")
    products = data_manager.get_products_by_category(category)
    
    if not products:
        text = f"""
📦 **{category}**

🚫 **No Products Available**

This category is currently empty, but don't worry - new products are added regularly!

💡 **What you can do:**
• Check other categories
• Set up notifications for new arrivals
• Contact us for special requests
"""
        keyboard = [
            [InlineKeyboardButton("🔔 Notify When Available", callback_data=f"notify_{category}")],
            [InlineKeyboardButton("🏠 Back to Menu", callback_data="menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        return
    
    # Enhanced product browsing with better layout
    visible_products = {k: v for k, v in products.items() if v.get('visible', True)}
    product_count = len(visible_products)
    
    # Fire sale indicator
    fire_sale_text = ""
    if data_manager.is_fire_sale_active():
        fire_sale_text = "\n🔥 **FIRE SALE ACTIVE - 25% OFF!** 🔥"
    
    text = f"""
📦 **{category}** ({product_count} items){fire_sale_text}

💎 **Premium Selection Available**

Select a product to view details, pricing, and add to cart:
"""
    
    keyboard = []
    
    # Sort products by grade (highest first) and then by name
    sorted_products = sorted(
        visible_products.items(),
        key=lambda x: (len(x[1].get('grade', '⭐')), x[1].get('name', '')),
        reverse=True
    )
    
    for product_id, product in sorted_products:
        product_name = product.get('name', 'Unknown Product')
        grade = product.get('grade', '⭐')
        
        # Enhanced price display with fire sale pricing
        prices = product.get('prices', {})
        base_price = None
        
        # Get the most common base size for this category
        size_priority = {
            '🌿 Flower': ['eighth', 'quarter', 'gram'],
            '🍯 Concentrates': ['gram'],
            '🍫 Edibles': ['unit'],
            '🚬 Pre-Rolls': ['single', 'unit']
        }
        
        priority_sizes = size_priority.get(category, ['unit', 'gram', 'eighth'])
        
        for size in priority_sizes:
            if size in prices:
                base_price = prices[size]
                break
        
        if not base_price and prices:
            base_price = list(prices.values())[0]
        
        # Apply fire sale discount if active
        display_price = base_price
        price_suffix = ""
        if base_price and data_manager.is_fire_sale_active():
            from utils import calculate_fire_sale_price
            display_price = calculate_fire_sale_price(base_price)
            price_suffix = f" ~~${base_price}~~"
        
        # Truncate long product names for better display
        from utils import truncate_text
        display_name = truncate_text(product_name, 25)
        
        button_text = f"{display_name} {grade}"
        keyboard.append([InlineKeyboardButton(
            button_text, 
            callback_data=f"view_{category}_{product_id}"
        )])
    
    # Category-specific action buttons
    action_buttons = []
    
    if category == "🌿 Flower":
        action_buttons.extend([
            [InlineKeyboardButton("🔥 Build Combo Deal", callback_data="combo_builder")],
            [InlineKeyboardButton("⚡ Quick Add Eighth", callback_data=f"quick_add_{category}")]
        ])
    elif category == "🔥 Combos/Deals":
        action_buttons.append([InlineKeyboardButton("🛠️ Create Custom Combo", callback_data="custom_combo")])
    
    # Always available actions (removed persistent navigation buttons)
    action_buttons.extend([
        [InlineKeyboardButton("🏠 Back to Menu", callback_data="menu")]
    ])
    
    keyboard.extend(action_buttons)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    # Handle both text and media messages
    try:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    except:
        # If editing fails (media message), send new message
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

async def handle_view_product(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle viewing a specific product with enhanced UI and quantity selectors."""
    parts = data.split("_", 2)  # view_category_productid
    if len(parts) != 3:
        await update.callback_query.edit_message_text("❌ Invalid product selection.")
        return
    
    category = parts[1]
    product_id = parts[2]
    
    product = data_manager.get_product(category, product_id)
    if not product:
        await update.callback_query.edit_message_text("❌ Product not found.")
        return
    
    # Enhanced product details display
    name = product.get('name', 'Unknown Product')
    grade = product.get('grade', '⭐')
    prices = product.get('prices', {})
    created_at = product.get('created_at', '')
    
    # Grade descriptions for better user understanding
    grade_descriptions = {
        '⭐⭐⭐': 'Low Za',
        '⭐⭐⭐⭐': 'High Za',
        '⭐⭐⭐⭐⭐': 'Topshelf'
    }
    grade_desc = grade_descriptions.get(grade, '')
    
    # Calculate savings if fire sale is active
    fire_sale_info = ""
    if data_manager.is_fire_sale_active():
        fire_sale_info = "\n🔥 **FIRE SALE - 25% OFF THIS ITEM!** 🔥"
    
    text = f"""
🌟 **{name}**

⭐ **Quality:** {grade} ({grade_desc})
📂 **Category:** {category}
🆕 **Status:** Recently Added{fire_sale_info}

💰 **Pricing & Sizes:**
"""
    
    # Enhanced pricing display with quantity selectors
    if prices:
        from utils import get_size_display_name, calculate_fire_sale_price
        
        for size, price in prices.items():
            size_display = get_size_display_name(size)
            
            # Show fire sale pricing
            if data_manager.is_fire_sale_active():
                sale_price = calculate_fire_sale_price(price)
                savings = price - sale_price
                text += f"• **{size_display}:** ~~${price}~~ **${sale_price}** (Save ${savings})\n"
            else:
                text += f"• **{size_display}:** **${price}**\n"
    
    text += "\n🛒 **Select size to add to cart:**"
    
    # Create enhanced size selection buttons with emojis
    keyboard = []
    
    # Size emoji mapping
    size_emojis = {
        'eighth': '🎱',  # 8-ball emoji
        'quarter': '🪙',  # coin emoji
        'half': '🥝',    # kiwi emoji
        'oz': '🧅',      # onion emoji
        '2oz': '🧅🧅',   # 2 onion emojis
        'qp': '🍔'       # burger emoji
    }
    
    for size, price in prices.items():
        size_display = get_size_display_name(size)
        emoji = size_emojis.get(size, '📦')  # default emoji if size not found
        
        # Apply fire sale discount
        display_price = price
        if data_manager.is_fire_sale_active():
            from utils import calculate_fire_sale_price
            display_price = calculate_fire_sale_price(price)
        
        # Add button with emoji
        keyboard.append([InlineKeyboardButton(
            f"{emoji} Add {size_display} - ${display_price}",
            callback_data=f"add_{category}_{product_id}_{size}"
        )])
    
    # Product actions
    action_buttons = [
        [InlineKeyboardButton("🏠 Back to Category", callback_data=f"category_{category}"),
         InlineKeyboardButton("🛒 View Cart", callback_data="cart")]
    ]
    
    keyboard.extend(action_buttons)
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send media if available with enhanced caption
    photo_id = product.get('photo_id')
    video_id = product.get('video_id')
    animation_id = product.get('animation_id')
    
    if animation_id:
        try:
            await update.callback_query.delete_message()
            await context.bot.send_animation(
                chat_id=update.effective_chat.id,
                animation=animation_id,
                caption=text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return
        except Exception as e:
            logger.error(f"Error sending animation: {e}")
    elif video_id:
        try:
            await update.callback_query.delete_message()
            await context.bot.send_video(
                chat_id=update.effective_chat.id,
                video=video_id,
                caption=text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return
        except Exception as e:
            logger.error(f"Error sending video: {e}")
    elif photo_id:
        try:
            await update.callback_query.delete_message()
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=photo_id,
                caption=text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return
        except Exception as e:
            logger.error(f"Error sending photo: {e}")
    
    # Handle both text and media messages
    try:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    except:
        # If editing fails (media message), send new message
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

async def handle_add_to_cart(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle adding product to cart."""
    logger.info(f"Processing add to cart callback: {data}")
    
    # Parse callback data: add_category_productid_size
    # Need to handle product IDs that contain underscores
    if not data.startswith("add_"):
        logger.error(f"Invalid add to cart action: {data}")
        await update.callback_query.answer("❌ Invalid add to cart action.")
        return
    
    # Remove "add_" prefix
    remaining = data[4:]  # Remove "add_"
    
    # Find the last underscore to separate size from product_id
    last_underscore = remaining.rfind("_")
    if last_underscore == -1:
        logger.error(f"Invalid add to cart action: {data}")
        await update.callback_query.answer("❌ Invalid add to cart action.")
        return
    
    size = remaining[last_underscore + 1:]
    before_size = remaining[:last_underscore]
    
    # Find the first underscore to separate category from product_id
    first_underscore = before_size.find("_")
    if first_underscore == -1:
        logger.error(f"Invalid add to cart action: {data}")
        await update.callback_query.answer("❌ Invalid add to cart action.")
        return
    
    category = before_size[:first_underscore]
    product_id = before_size[first_underscore + 1:]
    
    logger.info(f"Parsed - Category: {category}, Product ID: {product_id}, Size: {size}")
    
    user_id = update.effective_user.id
    
    product = data_manager.get_product(category, product_id)
    if not product:
        await update.callback_query.answer("❌ Product not found.")
        return
    
    price = product.get('prices', {}).get(size)
    if price is None:
        await update.callback_query.answer("❌ Size not available.")
        return
    
    # Create cart item
    cart_item = {
        'product_id': product_id,
        'category': category,
        'name': product.get('name'),
        'grade': product.get('grade'),
        'size': size,
        'price': price,
        'quantity': 1
    }
    
    # Add to cart
    data_manager.add_to_cart(user_id, cart_item)
    logger.info(f"Added item to cart for user {user_id}: {cart_item}")
    
    # Verify cart was updated
    cart = data_manager.get_user_cart(user_id)
    logger.info(f"Cart after adding item: {cart}")
    
    # Get size display name
    from utils import get_size_display_name
    size_display = get_size_display_name(size)
    
    # Send success message as a new message instead of editing
    success_text = f"✅ Added {product.get('name')} ({size_display}) to cart!\n\nWhat would you like to do next?"
    
    try:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=success_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🛒 View Cart", callback_data="cart")],
                [InlineKeyboardButton("➕ Continue Shopping", callback_data="menu")],
                [InlineKeyboardButton("✅ Checkout", callback_data="checkout")]
            ])
        )
        
        # Answer the callback query to remove the loading state
        await update.callback_query.answer("✅ Added to cart!")
    except Exception as e:
        logger.error(f"Error sending add to cart success message: {e}")
        # Fallback: just answer the callback query
        await update.callback_query.answer("✅ Added to cart!")

async def handle_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle cart view."""
    from handlers.command_handlers import cart
    await cart(update, context)

async def handle_clear_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle clearing cart."""
    user_id = update.effective_user.id
    data_manager.clear_cart(user_id)
    
    await update.callback_query.edit_message_text(
        "🗑️ Cart cleared!\n\nReady to start fresh?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🛍️ Browse Menu", callback_data="menu")]
        ])
    )

async def handle_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle enhanced checkout process with detailed order review."""
    user_id = update.effective_user.id
    cart_items = data_manager.get_user_cart(user_id)
    
    if not cart_items:
        await update.callback_query.edit_message_text(
            "🛒 Your cart is empty!\n\nAdd some products before checkout.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🛍️ Browse Menu", callback_data="menu")]
            ])
        )
        return
    
    # Check minimum order requirement
    user_region = data_manager.get_user_region(user_id)
    from config import REGIONS
    min_order = REGIONS.get(user_region, {}).get('min_order', 50)
    delivery_fee = REGIONS.get(user_region, {}).get('delivery_fee', 10)
    
    # Calculate totals
    subtotal = sum(item.get('price', 0) * item.get('quantity', 1) for item in cart_items)
    
    # Apply fire sale discount
    fire_sale_savings = 0
    if data_manager.is_fire_sale_active():
        for item in cart_items:
            original_price = item.get('price', 0)
            from utils import calculate_fire_sale_price
            discounted_price = calculate_fire_sale_price(original_price)
            fire_sale_savings += (original_price - discounted_price) * item.get('quantity', 1)
    
    total_after_discounts = subtotal - fire_sale_savings
    
    if total_after_discounts < min_order:
        shortage = min_order - total_after_discounts
        
        text = f"""
⚠️ **Minimum Order Not Met**

**Current Total:** ${total_after_discounts}
**Required Minimum:** ${min_order}
**Shortage:** ${shortage}

Add more items to meet the minimum order requirement for delivery.

💡 **Suggestions:**
• Add more flower strains
• Try our combo deals
• Explore edibles or concentrates
"""
        
        keyboard = [
            [InlineKeyboardButton("🛍️ Add More Items", callback_data="menu")],
            [InlineKeyboardButton("🔥 View Combo Deals", callback_data="category_🔥 Combos/Deals")],
            [InlineKeyboardButton("🏠 Back to Cart", callback_data="cart")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        return
    
    # Show address selection or prompt to add address
    addresses = data_manager.get_user_addresses(user_id)
    
    if not addresses:
        text = f"""
📍 **Delivery Address Required**

**Order Summary:**
• Items: {len(cart_items)}
• Subtotal: ${total_after_discounts}
• Delivery: ${delivery_fee}
• **Total: ${total_after_discounts + delivery_fee}**

Please provide your complete delivery address to continue.

Please enter your delivery address
"""
        
        keyboard = [
            [InlineKeyboardButton("📝 Enter Address Now", callback_data="request_address")],
            [InlineKeyboardButton("🏠 Back to Cart", callback_data="cart")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        context.user_data['awaiting_address'] = True
        return
    
    # Enhanced address selection with order preview
    item_count = len(cart_items)
    total_qty = sum(item.get('quantity', 1) for item in cart_items)
    final_total = total_after_discounts + delivery_fee
    
    # Delivery time estimate
    from utils import calculate_delivery_estimate
    delivery_estimate = calculate_delivery_estimate(user_region)
    
    text = f"""
📍 **Select Delivery Address**

📦 **Order Summary:**
• {item_count} item{'s' if item_count != 1 else ''} ({total_qty} units)
• Subtotal: ${total_after_discounts}
• Delivery: ${delivery_fee}
• **Total: ${final_total}**

Choose your delivery address:
"""
    
    keyboard = []
    
    for i, address in enumerate(addresses):
        address_label = address.get('label', f"Address {i+1}")
        address_preview = address.get('address', '')[:30] + "..." if len(address.get('address', '')) > 30 else address.get('address', '')
        
        keyboard.append([InlineKeyboardButton(
            f"📍 {address_label}: {address_preview}",
            callback_data=f"address_select_{i}"
        )])
    
    keyboard.extend([
        [InlineKeyboardButton("➕ Add New Address", callback_data="address_add")],
        [InlineKeyboardButton("💾 Save Order for Later", callback_data="save_order")],
        [InlineKeyboardButton("🏠 Back to Cart", callback_data="cart")]
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle notifications view."""
    from handlers.command_handlers import notifications
    await notifications(update, context)

async def handle_saved_addresses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle saved addresses management."""
    user_id = update.effective_user.id
    addresses = data_manager.get_user_addresses(user_id)
    
    if not addresses:
        text = """
📍 **Saved Addresses**

🏠 **No Saved Addresses**

You haven't saved any delivery addresses yet. Add addresses to speed up future checkouts!

💡 **Benefits of saving addresses:**
• Faster checkout process
• No need to re-type addresses
• Easy switching between locations
• Secure address storage
"""
        
        keyboard = [
            [InlineKeyboardButton("➕ Add New Address", callback_data="address_add")],
            [InlineKeyboardButton("🏠 Back to Menu", callback_data="menu")]
        ]
    else:
        text = f"""
📍 **Saved Addresses**

🏠 **Your Saved Locations** ({len(addresses)}/2)

"""
        
        # Display saved addresses
        for i, address in enumerate(addresses):
            address_label = address.get('label', f"Address {i+1}")
            address_text = address.get('address', 'No address')
            created_at = address.get('created_at', '')
            
            # Truncate long addresses for display
            display_address = address_text[:50] + "..." if len(address_text) > 50 else address_text
            
            text += f"**{i+1}. {address_label}**\n"
            text += f"📍 {display_address}\n\n"
        
        keyboard = []
        
        # Individual address management
        for i, address in enumerate(addresses):
            address_label = address.get('label', f"Address {i+1}")
            keyboard.append([
                InlineKeyboardButton(f"✏️ Edit {address_label}", callback_data=f"address_edit_{i}"),
                InlineKeyboardButton(f"🗑️ Delete", callback_data=f"address_delete_{i}")
            ])
        
        # Add new address if not at limit
        if len(addresses) < 2:
            keyboard.append([InlineKeyboardButton("➕ Add New Address", callback_data="address_add")])
        
        keyboard.append([InlineKeyboardButton("🏠 Back to Menu", callback_data="menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_mute_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle enhanced mute settings with category-specific options.""" 
    text = """
🔇 **Advanced Mute Settings**

🎯 **Mute by Category** - Choose specific notification types to mute:

📱 **Available Categories:**
• 🆕 **New Arrivals** - Product launch notifications
• 💰 **Price Alerts** - Sales and discount notifications  
• 🔥 **Fire Sales** - Limited-time flash sale alerts
• 🎯 **Combo Deals** - Special bundle offers
• 📦 **Order Updates** - Status and delivery notifications

Select a category to customize its mute settings:
"""
    
    keyboard = [
        [InlineKeyboardButton("🆕 New Arrivals", callback_data="mute_category_new_arrivals"),
         InlineKeyboardButton("💰 Price Alerts", callback_data="mute_category_price_alerts")],
        [InlineKeyboardButton("🔥 Fire Sales", callback_data="mute_category_fire_sales"),
         InlineKeyboardButton("🎯 Combo Deals", callback_data="mute_category_combo_deals")],
        [InlineKeyboardButton("📦 Order Updates", callback_data="mute_category_order_updates")],
        [InlineKeyboardButton("🌐 Mute All Categories", callback_data="mute_all_categories")],
        [InlineKeyboardButton("🏠 Back to Notifications", callback_data="notifications")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_mute_category(update: Update, context: ContextTypes.DEFAULT_TYPE, category: str):
    """Handle muting specific notification categories with timer selection."""
    category_names = {
        'new_arrivals': '🆕 New Arrivals',
        'price_alerts': '💰 Price Alerts', 
        'fire_sales': '🔥 Fire Sales',
        'combo_deals': '🎯 Combo Deals',
        'order_updates': '📦 Order Updates'
    }
    
    category_display = category_names.get(category, category.replace('_', ' ').title())
    
    text = f"""
🔇 **Mute {category_display}**

⏰ **Choose mute duration:**

Select how long you'd like to mute {category_display} notifications. You can always unmute earlier if needed.

💡 **Recommendations:**
• **1-3 days:** Quick break from notifications
• **7 days:** Weekly reset after large orders
• **12 days:** Extended quiet period
"""
    
    keyboard = []
    
    # Enhanced timer options with descriptions
    timer_descriptions = {
        1: "24 hours",
        2: "2 days (weekend)",
        3: "3 days (short break)",
        5: "5 days (work week)",
        7: "1 week (recommended)",
        10: "10 days (extended)",
        12: "12 days (maximum)"
    }
    
    # Create timer buttons in pairs
    for i in range(0, len(MUTE_TIMER_OPTIONS), 2):
        row = []
        for j in range(2):
            if i + j < len(MUTE_TIMER_OPTIONS):
                days = MUTE_TIMER_OPTIONS[i + j]
                description = timer_descriptions.get(days, f"{days} days")
                button_text = f"{days}d - {description}"
                row.append(InlineKeyboardButton(
                    button_text,
                    callback_data=f"apply_mute_{category}_{days}"
                ))
        keyboard.append(row)
    
    keyboard.extend([
        [InlineKeyboardButton("🔄 Choose Different Category", callback_data="mute_settings")],
        [InlineKeyboardButton("🏠 Back to Notifications", callback_data="notifications")]
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_apply_mute(update: Update, context: ContextTypes.DEFAULT_TYPE, category: str, days: int):
    """Apply mute settings and show confirmation."""
    user_id = update.effective_user.id
    
    # Apply the mute
    success = data_manager.set_user_mute(user_id, category, days)
    
    if success:
        category_names = {
            'new_arrivals': '🆕 New Arrivals',
            'price_alerts': '💰 Price Alerts',
            'fire_sales': '🔥 Fire Sales', 
            'combo_deals': '🎯 Combo Deals',
            'order_updates': '📦 Order Updates'
        }
        
        category_display = category_names.get(category, category.replace('_', ' ').title())
        day_text = "day" if days == 1 else "days"
        
        from datetime import datetime, timedelta
        unmute_date = (datetime.now() + timedelta(days=days)).strftime('%B %d at %I:%M %p')
        
        text = f"""
✅ **Mute Applied Successfully**

🔇 **{category_display}** notifications are now muted for **{days} {day_text}**.

📅 **Will automatically unmute:** {unmute_date}

💡 **What this means:**
• You won't receive {category_display.lower()} notifications
• Other notification types remain active
• You can unmute anytime in notification settings
• Important order updates will still be delivered

**Need to make changes?**
"""
        
        keyboard = [
            [InlineKeyboardButton("🔧 Adjust This Mute", callback_data=f"mute_category_{category}"),
             InlineKeyboardButton("🔕 Mute Another Category", callback_data="mute_settings")],
            [InlineKeyboardButton("🔊 Unmute Now", callback_data=f"unmute_category_{category}"),
             InlineKeyboardButton("📱 View All Mutes", callback_data="manage_mutes")],
            [InlineKeyboardButton("🏠 Back to Menu", callback_data="menu")]
        ]
        
        # Success feedback
        await update.callback_query.answer(f"✅ {category_display} muted for {days} {day_text}")
    else:
        text = """
❌ **Mute Failed**

There was an error applying your mute settings. Please try again.
"""
        
        keyboard = [
            [InlineKeyboardButton("🔄 Try Again", callback_data=f"mute_category_{category}")],
            [InlineKeyboardButton("🏠 Back to Notifications", callback_data="notifications")]
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_unmute_category(update: Update, context: ContextTypes.DEFAULT_TYPE, category: str):
    """Handle unmuting a specific category."""
    user_id = update.effective_user.id
    
    # Remove mute for specific category
    success = data_manager.remove_user_mute(user_id, category)
    
    if success:
        category_names = {
            'new_arrivals': '🆕 New Arrivals',
            'price_alerts': '💰 Price Alerts',
            'fire_sales': '🔥 Fire Sales',
            'combo_deals': '🎯 Combo Deals',
            'order_updates': '📦 Order Updates'
        }
        
        category_display = category_names.get(category, category.replace('_', ' ').title())
        
        await update.callback_query.edit_message_text(
            f"🔊 **{category_display} Unmuted**\n\nYou'll now receive {category_display.lower()} notifications again.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔇 Mute Another Category", callback_data="mute_settings")],
                [InlineKeyboardButton("🔔 Notification Settings", callback_data="notifications")],
                [InlineKeyboardButton("🏠 Back to Menu", callback_data="menu")]
            ])
        )
        
        await update.callback_query.answer(f"✅ {category_display} notifications restored")
    else:
        await update.callback_query.answer("❌ Error unmuting category")

async def handle_mute_action(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle general mute actions."""
    user_id = update.effective_user.id
    
    if data.startswith("mute_all_"):
        days = int(data.replace("mute_all_", ""))
        
        # Mute all categories
        for category in NOTIFICATION_CATEGORIES:
            data_manager.mute_notifications(user_id, category, days)
        
        await update.callback_query.edit_message_text(
            f"🔇 All notifications muted for {days} day{'s' if days > 1 else ''}!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Back to Menu", callback_data="menu")]
            ])
        )
    
    elif data.startswith("mute_post_order_"):
        days = int(data.replace("mute_post_order_", ""))
        
        # Mute specific categories after order
        categories_to_mute = ['new_arrivals', 'restocks', 'fire_sales']
        for category in categories_to_mute:
            data_manager.mute_notifications(user_id, category, days)
        
        await update.callback_query.edit_message_text(
            f"✅ Product alerts muted for {days} day{'s' if days > 1 else ''}!\n\nYou'll still receive order updates and admin messages.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Back to Menu", callback_data="menu")]
            ])
        )
    
    elif data == "no_mute":
        await update.callback_query.edit_message_text(
            "✅ Notifications will remain active!\n\nYou'll continue to receive all updates.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Back to Menu", callback_data="menu")]
            ])
        )

async def handle_quick_mute(update: Update, context: ContextTypes.DEFAULT_TYPE, days: int):
    """Handle quick mute for specified days."""
    user_id = update.effective_user.id
    
    # Mute all categories for specified days
    for category in NOTIFICATION_CATEGORIES:
        data_manager.mute_notifications(user_id, category, days)
    
    await update.callback_query.edit_message_text(
        f"🔇 All notifications muted for {days} day{'s' if days > 1 else ''}!\n\nYou'll still receive important order updates.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Back to Menu", callback_data="menu")]
        ])
    )

async def handle_mute_all(update: Update, context: ContextTypes.DEFAULT_TYPE, days: int):
    """Handle mute all notifications for specified days."""
    user_id = update.effective_user.id
    
    # Mute all categories for specified days
    for category in NOTIFICATION_CATEGORIES:
        data_manager.mute_notifications(user_id, category, days)
    
    await update.callback_query.edit_message_text(
        f"🔇 All notifications muted for {days} day{'s' if days > 1 else ''}!\n\nYou'll still receive important order updates.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Back to Menu", callback_data="menu")]
        ])
    )

async def handle_notification_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle notification history view."""
    user_id = update.effective_user.id
    
    # Get user's notification history (placeholder implementation)
    text = """
📊 **Notification History**

🔔 **Recent Activity:**
• No recent notifications

📈 **Statistics:**
• Total notifications received: 0
• Muted categories: 0
• Active alerts: 0

💡 **Tips:**
• Enable notifications to stay updated on new products
• Use category-specific mutes for better control
• Check back regularly for new arrivals
"""
    
    keyboard = [
        [InlineKeyboardButton("🔔 Notification Settings", callback_data="notifications")],
        [InlineKeyboardButton("🏠 Back to Menu", callback_data="menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_notification_advanced(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle advanced notification settings."""
    text = """
⚙️ **Advanced Notification Settings**

🎯 **Customization Options:**

📱 **Delivery Preferences:**
• Quiet hours: 10 PM - 8 AM
• Weekend notifications: Enabled
• Priority alerts: Always on

🔔 **Smart Features:**
• Location-based alerts: Enabled
• Price drop notifications: Enabled
• Restock alerts: Enabled

⚡ **Quick Actions:**
"""
    
    keyboard = [
        [InlineKeyboardButton("🔇 Mute All (1 week)", callback_data="mute_all_7"),
         InlineKeyboardButton("⏸️ Pause All (24h)", callback_data="mute_all_1")],
        [InlineKeyboardButton("🔧 Category Settings", callback_data="mute_categories"),
         InlineKeyboardButton("📊 View History", callback_data="notification_history")],
        [InlineKeyboardButton("🏠 Back to Notifications", callback_data="notifications")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_manage_mutes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle viewing and managing all active mutes."""
    user_id = update.effective_user.id
    settings = data_manager.get_user_notification_settings(user_id)
    muted_categories = settings.get('muted_categories', {})
    
    if not muted_categories:
        text = """
📱 **Manage Mutes**

🔔 **No Active Mutes**

All your notification categories are currently active.

💡 **Quick Actions:**
"""
        
        keyboard = [
            [InlineKeyboardButton("🔇 Mute Categories", callback_data="mute_settings")],
            [InlineKeyboardButton("⏰ Quick Mute (3 days)", callback_data="quick_mute_3")],
            [InlineKeyboardButton("🏠 Back to Notifications", callback_data="notifications")]
        ]
    else:
        text = """
📱 **Manage Active Mutes**

🔕 **Currently Muted Categories:**

"""
        
        # Show active mutes with time remaining
        from datetime import datetime
        current_time = datetime.now()
        
        for category, mute_data in muted_categories.items():
            try:
                mute_until = datetime.fromisoformat(mute_data['muted_until'])
                if current_time < mute_until:
                    time_diff = mute_until - current_time
                    days_left = time_diff.days
                    hours_left = time_diff.seconds // 3600
                    
                    if days_left > 0:
                        time_text = f"{days_left} day{'s' if days_left != 1 else ''}"
                    elif hours_left > 0:
                        time_text = f"{hours_left} hour{'s' if hours_left != 1 else ''}"
                    else:
                        time_text = "Less than 1 hour"
                    
                    category_display = category.replace('_', ' ').title()
                    text += f"• 🔕 **{category_display}**: {time_text} remaining\n"
            except:
                # Remove invalid mute data
                data_manager.remove_user_mute(user_id, category)
        
        text += "\n**Quick Actions:**"
        
        keyboard = []
        
        # Individual unmute buttons
        active_mutes = []
        for category, mute_data in muted_categories.items():
            try:
                mute_until = datetime.fromisoformat(mute_data['muted_until'])
                if current_time < mute_until:
                    active_mutes.append(category)
            except:
                pass
        
        # Create unmute buttons in pairs
        for i in range(0, len(active_mutes), 2):
            row = []
            for j in range(2):
                if i + j < len(active_mutes):
                    category = active_mutes[i + j]
                    category_display = category.replace('_', ' ').title()[:15]
                    row.append(InlineKeyboardButton(
                        f"🔊 {category_display}",
                        callback_data=f"unmute_category_{category}"
                    ))
            keyboard.append(row)
        
        keyboard.extend([
            [InlineKeyboardButton("🔊 Unmute All", callback_data="unmute_all")],
            [InlineKeyboardButton("🔇 Add More Mutes", callback_data="mute_settings")],
            [InlineKeyboardButton("🏠 Back to Notifications", callback_data="notifications")]
        ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_post_order_mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle post-order mute suggestion."""
    text = """
💡 **Post-Order Mute Suggestion**

Since you just placed an order, you might want to mute notifications for a while to avoid unnecessary alerts while you enjoy your purchase.

🔇 **Recommended Mute Duration:**
"""
    
    keyboard = [
        [InlineKeyboardButton("🔇 Mute for 7 days (Recommended)", callback_data="apply_post_order_mute_7")],
        [InlineKeyboardButton("🔕 Mute for 3 days", callback_data="apply_post_order_mute_3")],
        [InlineKeyboardButton("⏸️ Mute for 10 days", callback_data="apply_post_order_mute_10")],
        [InlineKeyboardButton("🔔 Keep Notifications On", callback_data="notifications")],
        [InlineKeyboardButton("🏠 Back to Menu", callback_data="menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_apply_post_order_mute(update: Update, context: ContextTypes.DEFAULT_TYPE, days: int):
    """Handle applying post-order mute for specified days."""
    user_id = update.effective_user.id
    
    # Mute all categories except order updates
    muted_count = 0
    for category in NOTIFICATION_CATEGORIES:
        if category != 'order_updates':  # Keep order updates active
            if data_manager.set_user_mute(user_id, category, days):
                muted_count += 1
    
    day_text = "day" if days == 1 else "days"
    
    text = f"""
✅ **Post-Order Mute Applied**

🔇 **{muted_count} notification categories muted for {days} {day_text}**

💡 **What's muted:**
• New product arrivals
• Price alerts & sales
• Fire sale notifications  
• Combo deal alerts

🔔 **Still active:**
• Order status updates
• Delivery notifications

You can adjust these settings anytime in notification preferences.
"""
    
    keyboard = [
        [InlineKeyboardButton("🔧 Adjust Mute Settings", callback_data="manage_mutes")],
        [InlineKeyboardButton("🔔 Notification Settings", callback_data="notifications")],
        [InlineKeyboardButton("🏠 Back to Menu", callback_data="menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    await update.callback_query.answer(f"✅ Notifications muted for {days} {day_text}")

async def handle_unmute_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle unmuting all notifications."""
    user_id = update.effective_user.id
    
    # Remove all mutes
    unmuted_count = 0
    for category in NOTIFICATION_CATEGORIES:
        if data_manager.remove_user_mute(user_id, category):
            unmuted_count += 1
    
    if unmuted_count > 0:
        text = f"""
🔊 **All Notifications Restored**

✅ **{unmuted_count} notification categories unmuted**

You'll now receive all types of notifications:
• 🆕 New product arrivals
• 💰 Price alerts & sales
• 🔥 Fire sale notifications
• 🎯 Combo deal alerts
• 📦 Order status updates

Ready to stay updated on all our latest offerings!
"""
        
        await update.callback_query.answer("🔊 All notifications restored!")
    else:
        text = """
🔔 **Notifications Already Active**

All your notification categories were already unmuted. You're receiving all updates!
"""
        
        await update.callback_query.answer("ℹ️ Notifications were already active")
    
    keyboard = [
        [InlineKeyboardButton("🔇 Mute Categories", callback_data="mute_settings")],
        [InlineKeyboardButton("🔔 Notification Settings", callback_data="notifications")],
        [InlineKeyboardButton("🏠 Back to Menu", callback_data="menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_notify_when_available(update: Update, context: ContextTypes.DEFAULT_TYPE, category: str):
    """Handle notification signup for when products become available in a category."""
    user_id = update.effective_user.id
    
    # Category display names
    category_names = {
        '🌿 Flower': '🌿 Flower Products',
        '🍯 Concentrates': '🍯 Concentrates & Extracts',
        '🍫 Edibles': '🍫 Edibles & Treats',
        '🚬 Pre-Rolls': '🚬 Pre-Rolls & Joints',
        '🔥 Combos/Deals': '🔥 Combo Deals',
        '👻 Hidden Menu': '👻 Hidden Menu Items'
    }
    
    category_display = category_names.get(category, category)
    
    # Add user to notification list for this category
    notification_key = f"category_availability_{category}"
    
    # Store in user settings (you can expand data_manager to support this)
    user_settings = data_manager.get_user_notification_settings(user_id)
    if 'availability_notifications' not in user_settings:
        user_settings['availability_notifications'] = []
    
    if category not in user_settings['availability_notifications']:
        user_settings['availability_notifications'].append(category)
        
        # Save updated settings
        data_manager.user_notification_settings[user_id] = user_settings
        
        text = f"""
✅ **Notification Activated**

🔔 **You'll be notified when {category_display} become available!**

📱 **What happens next:**
• You'll get an instant alert when new products are added to {category}
• Notifications include product names, prices, and quick purchase links
• You can disable this anytime in notification settings

💡 **Smart Notifications:**
• Only sent when genuinely new products arrive
• Respects your mute settings (if category notifications are muted)
• Includes premium product previews and early access info

🎯 **Want more control?**
"""
        
        keyboard = [
            [InlineKeyboardButton("🔔 Manage All Notifications", callback_data="notifications")],
            [InlineKeyboardButton("📱 Other Category Alerts", callback_data="setup_more_alerts")],
            [InlineKeyboardButton("🏠 Back to Menu", callback_data="menu")]
        ]
        
        await update.callback_query.answer("🔔 Notification activated!")
        
    else:
        text = f"""
ℹ️ **Already Subscribed**

🔔 **You're already signed up for {category_display} notifications!**

📊 **Current Status:**
• ✅ Active notification for new {category} products
• 🔔 Alerts enabled and ready
• 📱 Instant notifications when products arrive

🎛️ **Manage Your Alerts:**
"""
        
        keyboard = [
            [InlineKeyboardButton("🔕 Disable This Alert", callback_data=f"disable_notify_{category}")],
            [InlineKeyboardButton("🔔 All Notification Settings", callback_data="notifications")],
            [InlineKeyboardButton("🏠 Back to Menu", callback_data="menu")]
        ]
        
        await update.callback_query.answer("ℹ️ Already subscribed to this category")
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_setup_more_alerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle setting up notifications for multiple categories."""
    user_id = update.effective_user.id
    user_settings = data_manager.get_user_notification_settings(user_id)
    active_notifications = user_settings.get('availability_notifications', [])
    
    text = """
📱 **Category Alert Setup**

🔔 **Choose categories to get notified about new arrivals:**

Select categories you'd like to monitor for new product arrivals. You'll get instant alerts when new items are added.
"""
    
    keyboard = []
    
    # Category options with status indicators
    category_options = [
        ('🌿 Flower', '🌿 Flower'),
        ('🍯 Concentrates', '🍯 Concentrates'), 
        ('🍫 Edibles', '🍫 Edibles'),
        ('🚬 Pre-Rolls', '🚬 Pre-Rolls'),
        ('🔥 Combos/Deals', '🔥 Combos/Deals')
    ]
    
    for category_key, category_display in category_options:
        if category_key in active_notifications:
            status = "✅ Active"
            action = f"disable_notify_{category_key}"
        else:
            status = "⭕ Inactive" 
            action = f"notify_{category_key}"
        
        keyboard.append([InlineKeyboardButton(
            f"{category_display} - {status}",
            callback_data=action
        )])
    
    keyboard.extend([
        [InlineKeyboardButton("🔔 Notification Settings", callback_data="notifications")],
        [InlineKeyboardButton("🏠 Back to Menu", callback_data="menu")]
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_disable_notify(update: Update, context: ContextTypes.DEFAULT_TYPE, category: str):
    """Handle disabling category availability notifications."""
    user_id = update.effective_user.id
    user_settings = data_manager.get_user_notification_settings(user_id)
    active_notifications = user_settings.get('availability_notifications', [])
    
    if category in active_notifications:
        active_notifications.remove(category)
        user_settings['availability_notifications'] = active_notifications
        data_manager.user_notification_settings[user_id] = user_settings
        
        category_display = category.replace('_', ' ').title()
        
        text = f"""
🔕 **Notification Disabled**

✅ **{category_display} availability alerts have been turned off.**

📱 **What this means:**
• You won't receive alerts for new {category_display.lower()} products
• Other notification types remain active
• You can re-enable this anytime

💡 **Want to stay updated differently?**
"""
        
        keyboard = [
            [InlineKeyboardButton("🔔 Re-enable This Alert", callback_data=f"notify_{category}")],
            [InlineKeyboardButton("📱 Manage Other Alerts", callback_data="setup_more_alerts")],
            [InlineKeyboardButton("🔔 All Notifications", callback_data="notifications")],
            [InlineKeyboardButton("🏠 Back to Menu", callback_data="menu")]
        ]
        
        await update.callback_query.answer("🔕 Alert disabled")
    else:
        await update.callback_query.answer("ℹ️ Alert was already disabled")
        # Redirect to setup page
        await handle_setup_more_alerts(update, context)
        return
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_address_action(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle address-related actions."""
    user_id = update.effective_user.id
    
    if data.startswith("address_select_"):
        address_index = int(data.replace("address_select_", ""))
        addresses = data_manager.get_user_addresses(user_id)
        
        if 0 <= address_index < len(addresses):
            address = addresses[address_index]
            from handlers.message_handlers import create_order_with_address
            await create_order_with_address(update, context, address)
        else:
            await update.callback_query.edit_message_text("❌ Invalid address selection.")
    
    elif data == "address_add":
        logger.info(f"Setting awaiting_address=True for user {update.effective_user.id}")
        await update.callback_query.edit_message_text(
            "📍 **Add New Address**\n\nPlease send your delivery address:"
        )
        context.user_data['awaiting_address'] = True
    
    elif data == "request_address":
        logger.info(f"Setting awaiting_address=True for user {update.effective_user.id}")
        await update.callback_query.edit_message_text(
            "📍 **Enter Delivery Address**\n\nPlease send your complete delivery address:"
        )
        context.user_data['awaiting_address'] = True

async def handle_confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle order confirmation by admin."""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.callback_query.answer("❌ Access denied.")
        return
    
    order_id = data.replace("confirm_order_", "")
    order = data_manager.get_order_by_id(order_id)
    
    if not order:
        await update.callback_query.answer("❌ Order not found.")
        return
    
    # Update order status to approved (automatically paid)
    data_manager.update_order_status(order_id, 'approved', user_id)
    
    # Notify customer
    customer_id = order.get('user_id')
    if customer_id:
        try:
            await context.bot.send_message(
                chat_id=customer_id,
                text=f"✅ **Order Approved!**\n\nYour order {order_id} has been confirmed and marked as paid.\n\nEstimated delivery time: {calculate_estimated_delivery_time(data_manager.get_user_region(customer_id))}",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Failed to notify customer {customer_id}: {e}")
    
    await update.callback_query.edit_message_text(f"✅ Order {order_id} approved and marked as paid!")

async def handle_accept_order(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle order acceptance by admin."""
    await handle_confirm_order(update, context, data.replace("accept_order_", "confirm_order_"))

async def handle_reject_order(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle order rejection by admin."""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.callback_query.answer("❌ Access denied.")
        return
    
    order_id = data.replace("reject_order_", "")
    order = data_manager.get_order_by_id(order_id)
    
    if not order:
        await update.callback_query.answer("❌ Order not found.")
        return
    
    # Update order status to rejected
    data_manager.update_order_status(order_id, 'rejected', user_id)
    
    # Notify customer
    customer_id = order.get('user_id')
    if customer_id:
        try:
            await context.bot.send_message(
                chat_id=customer_id,
                text=f"❌ **Order Declined**\n\nSorry, your order {order_id} could not be processed at this time. Please contact us for more information.",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Failed to notify customer {customer_id}: {e}")
    
    await update.callback_query.edit_message_text(f"❌ Order {order_id} rejected.")

async def handle_remove_from_cart(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle removing item from cart."""
    user_id = update.effective_user.id
    cart_index = int(data.replace("remove_cart_", ""))
    
    if data_manager.remove_from_cart(user_id, cart_index):
        await update.callback_query.answer("✅ Item removed from cart")
        # Refresh cart view
        await handle_cart(update, context)
    else:
        await update.callback_query.answer("❌ Failed to remove item")

async def handle_fire_sale_action(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle fire sale actions."""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.callback_query.answer("❌ Access denied.")
        return
    
    if data == "fire_start":
        # TODO: Implement fire sale start workflow
        await update.callback_query.edit_message_text(
            "🔥 **Start Fire Sale**\n\nFire sale management coming soon!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Back to Admin", callback_data="admin")]
            ])
        )
    
    elif data == "fire_end":
        if data_manager.end_fire_sale(user_id):
            await update.callback_query.edit_message_text(
                "⏹️ Fire sale ended successfully!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏠 Back to Admin", callback_data="admin")]
                ])
            )
        else:
            await update.callback_query.edit_message_text(
                "❌ No active fire sale to end.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏠 Back to Admin", callback_data="admin")]
                ])
            )

async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin callback - show admin control panel."""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.callback_query.edit_message_text("❌ Access denied. Admin privileges required.")
        return
    
    text = """
🔧 **Admin Control Panel**

Select an action:
"""
    
    keyboard = [
        [InlineKeyboardButton("📦 Pending Orders", callback_data="admin_orders")],
        [InlineKeyboardButton("📍 Region Alerts", callback_data="admin_region_alerts")],
        [InlineKeyboardButton("🔥 Fire Sale", callback_data="admin_fire_sale")],
        [InlineKeyboardButton("🎯 Create Combo", callback_data="admin_create_combo")],
        [InlineKeyboardButton("📊 Statistics", callback_data="admin_stats")],
        [InlineKeyboardButton("⚙️ Settings", callback_data="admin_settings")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle admin actions."""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.callback_query.edit_message_text("❌ Access denied.")
        return
    
    action = data.replace("admin_", "")
    
    if action == "orders":
        await show_pending_orders(update, context)
    elif action == "region_alerts":
        await show_region_alert_options(update, context)
    elif action == "fire_sale":
        await show_fire_sale_options(update, context)
    elif action == "create_combo":
        await show_combo_creation(update, context)
    elif action == "stats":
        await show_admin_stats(update, context)
    elif action == "settings":
        await show_admin_settings(update, context)

async def show_pending_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show pending orders for admin review."""
    pending_orders = data_manager.get_pending_orders()
    
    if not pending_orders:
        await update.callback_query.edit_message_text(
            "📦 **Pending Orders**\n\nNo pending orders at the moment.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Back to Admin", callback_data="admin")]
            ])
        )
        return
    
    text = f"📦 **Pending Orders** ({len(pending_orders)})\n\n"
    keyboard = []
    
    for order in pending_orders[:5]:  # Show max 5 orders
        order_id = order.get('order_id', 'N/A')
        total = order.get('total_price', 0)
        customer_name = order.get('user_info', {}).get('first_name', 'Unknown')
        
        text += f"**{order_id}** - ${total} - {customer_name}\n"
        keyboard.append([
            InlineKeyboardButton(f"✅ Accept {order_id}", callback_data=f"accept_order_{order_id}"),
            InlineKeyboardButton(f"❌ Reject {order_id}", callback_data=f"reject_order_{order_id}")
        ])
    
    if len(pending_orders) > 5:
        text += f"\n... and {len(pending_orders) - 5} more orders"
    
    keyboard.append([InlineKeyboardButton("🏠 Back to Admin", callback_data="admin")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_region_alert_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show region alert options."""
    text = "📍 **Send Region Alert**\n\nSelect a region to send arrival notifications:"
    
    keyboard = []
    for region_id, region_data in REGIONS.items():
        keyboard.append([InlineKeyboardButton(
            region_data['name'],
            callback_data=f"alert_region_{region_id}"
        )])
    
    keyboard.append([InlineKeyboardButton("🏠 Back to Admin", callback_data="admin")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_fire_sale_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show enhanced fire sale management interface."""
    fire_sale_active = data_manager.is_fire_sale_active()
    
    # Calculate potential impact
    total_products = sum(len(products) for products in data_manager.fallback_products.values())
    visible_products = sum(len([p for p in products.values() if p.get('visible', True)]) 
                          for products in data_manager.fallback_products.values())
    
    # Estimate affected revenue
    active_carts = len([cart for cart in data_manager.user_cart.values() if cart])
    total_cart_value = 0
    for cart in data_manager.user_cart.values():
        for item in cart:
            total_cart_value += item.get('price', 0) * item.get('quantity', 1)
    
    if fire_sale_active:
        status_icon = "🔥"
        status_text = "**ACTIVE**"
        status_color = "🟢"
        impact_text = f"25% discount applied to {visible_products} products"
        
        # Calculate current savings
        potential_savings = total_cart_value * 0.25
        
        main_text = f"""
🔥 **Fire Sale Management Dashboard**

📊 **Current Status:** {status_color} {status_text}

🎯 **Active Impact:**
• Products on sale: **{visible_products}** items
• Discount rate: **25% OFF** everything
• Active carts affected: **{active_carts}**
• Estimated customer savings: **${potential_savings:.2f}**

⚠️ **Administrative Control:**
The fire sale is currently active. All visible products are automatically discounted by 25%.

💡 **Fire Sale Benefits:**
• Increased customer engagement
• Higher conversion rates
• Inventory movement acceleration
• Customer acquisition boost
"""
        
        keyboard = [
            [InlineKeyboardButton("⏹️ End Fire Sale", callback_data="fire_end_confirm")],
            [InlineKeyboardButton("📊 View Fire Sale Analytics", callback_data="fire_analytics")],
            [InlineKeyboardButton("📢 Send Fire Sale Alert", callback_data="fire_alert_all")],
            [InlineKeyboardButton("⏰ Schedule Auto-End", callback_data="fire_schedule_end")],
            [InlineKeyboardButton("🏠 Back to Admin", callback_data="admin")]
        ]
        
    else:
        status_icon = "⏸️"
        status_text = "**INACTIVE**"
        status_color = "🔴"
        impact_text = "Ready to launch 25% discount on all products"
        
        # Calculate potential impact
        estimated_boost = total_cart_value * 1.4  # Estimated 40% sales boost
        
        main_text = f"""
🔥 **Fire Sale Management Dashboard**

📊 **Current Status:** {status_color} {status_text}

🎯 **Launch Readiness:**
• Products ready for sale: **{visible_products}** items
• Potential discount rate: **25% OFF**
• Active shoppers to notify: **{active_carts}**
• Estimated sales boost: **${estimated_boost:.2f}**

💡 **Fire Sale Strategy:**
Fire sales create urgency and drive immediate purchases. Perfect for:
• Moving inventory quickly
• Attracting new customers  
• Boosting weekend sales
• Clearing seasonal stock

🚀 **Launch Options:**
"""
        
        keyboard = [
            [InlineKeyboardButton("🔥 Start Fire Sale Now", callback_data="fire_start_confirm")],
            [InlineKeyboardButton("⏰ Schedule Fire Sale", callback_data="fire_schedule")],
            [InlineKeyboardButton("🎯 Targeted Fire Sale", callback_data="fire_targeted")],
            [InlineKeyboardButton("📊 Preview Impact", callback_data="fire_preview")],
            [InlineKeyboardButton("🏠 Back to Admin", callback_data="admin")]
        ]
    
    text = main_text
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_region_alert_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show enhanced region alert broadcasting interface."""
    from config import REGIONS
    
    # Calculate users per region
    region_stats = {}
    for user_id, region in data_manager.user_regions.items():
        region_stats[region] = region_stats.get(region, 0) + 1
    
    total_users = sum(region_stats.values())
    
    text = f"""
📍 **Region Alert Broadcasting**

📊 **User Distribution:**
• Total registered users: **{total_users}**

"""
    
    # Show region breakdown
    for region_id, region_data in REGIONS.items():
        region_name = region_data['name']
        user_count = region_stats.get(region_id, 0)
        percentage = (user_count / max(total_users, 1)) * 100
        
        text += f"• {region_name}: **{user_count}** users ({percentage:.1f}%)\n"
    
    text += f"""

📢 **Alert Types Available:**
• 🆕 **New Product Arrivals** - Product launch announcements
• 🚛 **Delivery Updates** - Service area changes
• 🔥 **Flash Sales** - Limited-time regional offers
• 📦 **Inventory Alerts** - Low stock warnings
• 🎯 **Custom Messages** - Personalized announcements

**Choose a region to send targeted alerts:**
"""
    
    keyboard = []
    
    # Region selection with user counts
    for region_id, region_data in REGIONS.items():
        region_name = region_data['name']
        user_count = region_stats.get(region_id, 0)
        
        if user_count > 0:
            button_text = f"{region_name} ({user_count} users)"
            keyboard.append([InlineKeyboardButton(
                button_text,
                callback_data=f"alert_region_{region_id}"
            )])
    
    # Broadcast options
    if total_users > 0:
        keyboard.extend([
            [InlineKeyboardButton("📢 Broadcast to All Regions", callback_data="alert_all_regions")],
            [InlineKeyboardButton("🎯 Custom Regional Message", callback_data="alert_custom")],
            [InlineKeyboardButton("📊 Alert Analytics", callback_data="alert_analytics")]
        ])
    else:
        keyboard.append([InlineKeyboardButton("⚠️ No Users to Alert", callback_data="admin")])
    
    keyboard.append([InlineKeyboardButton("🏠 Back to Admin", callback_data="admin")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_combo_creation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show combo creation interface."""
    text = """
🎯 **Create Custom Combo**

Build custom product combinations with special pricing.

Coming soon!
"""
    
    keyboard = [[InlineKeyboardButton("🏠 Back to Admin", callback_data="admin")]]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show comprehensive admin statistics dashboard."""
    # Enhanced statistics calculation
    total_users = len(data_manager.user_regions)
    all_orders = []
    for user_orders in data_manager.user_orders.values():
        all_orders.extend(user_orders)
    
    total_orders = len(all_orders)
    pending_orders = len([order for order in all_orders if order.get('status') == 'pending'])
    completed_orders = len([order for order in all_orders if order.get('status') == 'delivered'])
    
    # Revenue calculations
    total_revenue = sum(order.get('total_price', 0) for order in all_orders if order.get('status') in ['delivered', 'confirmed'])
    pending_revenue = sum(order.get('total_price', 0) for order in all_orders if order.get('status') == 'pending')
    
    # Product statistics
    total_products = sum(len(products) for products in data_manager.fallback_products.values())
    visible_products = sum(len([p for p in products.values() if p.get('visible', True)]) 
                          for products in data_manager.fallback_products.values())
    
    # Category breakdown
    category_stats = []
    for category, products in data_manager.fallback_products.items():
        if products:
            visible_count = len([p for p in products.values() if p.get('visible', True)])
            category_stats.append(f"• {category}: {visible_count} products")
    
    # User engagement stats
    active_carts = len([cart for cart in data_manager.user_cart.values() if cart])
    total_cart_items = sum(len(cart) for cart in data_manager.user_cart.values())
    
    # Recent activity (last 24 hours)
    from datetime import datetime, timedelta
    yesterday = datetime.now() - timedelta(days=1)
    recent_orders = []
    try:
        recent_orders = [order for order in all_orders 
                        if datetime.fromisoformat(order.get('created_at', '')) > yesterday]
    except:
        pass
    
    # Fire sale status
    fire_sale_status = "🔥 ACTIVE" if data_manager.is_fire_sale_active() else "⏸️ Inactive"
    
    text = f"""
📊 **Admin Analytics Dashboard**

🕒 **Last Updated:** {get_current_time().strftime('%B %d, %Y at %I:%M %p')}

👥 **USER METRICS**
• Total Registered Users: **{total_users}**
• Active Shopping Carts: **{active_carts}**
• Total Cart Items: **{total_cart_items}**

📦 **ORDER STATISTICS**
• Total Orders: **{total_orders}**
• Pending Review: **{pending_orders}** ⚠️
• Completed Orders: **{completed_orders}** ✅
• Orders Today: **{len(recent_orders)}**

💰 **REVENUE TRACKING**
• Total Revenue: **${total_revenue:,.2f}**
• Pending Revenue: **${pending_revenue:,.2f}**
• Average Order: **${(total_revenue/max(completed_orders, 1)):,.2f}**

🌿 **PRODUCT INVENTORY**
• Total Products: **{total_products}**
• Visible/Active: **{visible_products}**
• Hidden Products: **{total_products - visible_products}**

📂 **Category Breakdown:**
{chr(10).join(category_stats) if category_stats else "• No products available"}

🔥 **SYSTEM STATUS**
• Fire Sale: {fire_sale_status}
• Bot Status: 🟢 Online
• Data Sync: ✅ Current

**📈 Performance Indicators:**
"""
    
    # Performance indicators
    if total_orders > 0:
        completion_rate = (completed_orders / total_orders) * 100
        text += f"• Order Completion Rate: **{completion_rate:.1f}%**\n"
    
    if pending_orders > 0:
        text += f"• Response Needed: **{pending_orders} orders awaiting review**\n"
    else:
        text += "• Response Status: ✅ **All orders processed**\n"
    
    if total_users > 0:
        engagement_rate = (active_carts / total_users) * 100
        text += f"• User Engagement: **{engagement_rate:.1f}%** have active carts\n"
    
    # Enhanced action buttons
    keyboard = [
        [InlineKeyboardButton("📦 Manage Orders", callback_data="admin_orders"),
         InlineKeyboardButton("📈 Detailed Analytics", callback_data="admin_detailed_stats")],
        [InlineKeyboardButton("👥 User Management", callback_data="admin_users"),
         InlineKeyboardButton("🌿 Product Overview", callback_data="admin_products")],
        [InlineKeyboardButton("💰 Revenue Reports", callback_data="admin_revenue"),
         InlineKeyboardButton("🔥 Fire Sale Toggle", callback_data="admin_fire_sale")],
        [InlineKeyboardButton("📊 Export Data", callback_data="admin_export"),
         InlineKeyboardButton("🔄 Refresh Stats", callback_data="admin_stats")],
        [InlineKeyboardButton("🏠 Back to Admin", callback_data="admin")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

# Cart Quantity Management Handlers
async def handle_decrease_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle decreasing item quantity in cart."""
    try:
        item_index = int(data.split("_")[-1])
        user_id = update.effective_user.id
        cart_items = data_manager.get_user_cart(user_id)
        
        if 0 <= item_index < len(cart_items):
            current_qty = cart_items[item_index].get('quantity', 1)
            if current_qty > 1:
                data_manager.update_cart_item_quantity(user_id, item_index, current_qty - 1)
                await update.callback_query.answer("✅ Quantity decreased")
            else:
                # Remove item if quantity would be 0
                data_manager.remove_from_cart(user_id, item_index)
                await update.callback_query.answer("🗑️ Item removed from cart")
            
            # Refresh cart view
            from handlers.command_handlers import cart
            await cart(update, context)
        else:
            await update.callback_query.answer("❌ Item not found")
    except (ValueError, IndexError):
        await update.callback_query.answer("❌ Invalid action")

async def handle_increase_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle increasing item quantity in cart."""
    try:
        item_index = int(data.split("_")[-1])
        user_id = update.effective_user.id
        cart_items = data_manager.get_user_cart(user_id)
        
        if 0 <= item_index < len(cart_items):
            current_qty = cart_items[item_index].get('quantity', 1)
            if current_qty < 10:  # Max quantity limit
                data_manager.update_cart_item_quantity(user_id, item_index, current_qty + 1)
                await update.callback_query.answer("✅ Quantity increased")
                
                # Refresh cart view
                from handlers.command_handlers import cart
                await cart(update, context)
            else:
                await update.callback_query.answer("⚠️ Maximum quantity reached (10)")
        else:
            await update.callback_query.answer("❌ Item not found")
    except (ValueError, IndexError):
        await update.callback_query.answer("❌ Invalid action")

async def handle_quantity_selector(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle quantity selector interface."""
    parts = data.split("_", 3)  # qty_select_category_productid_size
    if len(parts) != 4:
        await update.callback_query.answer("❌ Invalid selection")
        return
    
    category = parts[2]
    product_id = parts[3]
    size = parts[4] if len(parts) > 4 else parts[3].split("_")[-1]
    
    product = data_manager.get_product(category, product_id)
    if not product:
        await update.callback_query.answer("❌ Product not found")
        return
    
    name = product.get('name', 'Unknown Product')
    price = product.get('prices', {}).get(size, 0)
    
    # Apply fire sale discount
    if data_manager.is_fire_sale_active():
        from utils import calculate_fire_sale_price
        price = calculate_fire_sale_price(price)
    
    from utils import get_size_display_name
    size_display = get_size_display_name(size)
    
    text = f"""
🔢 **Quantity Selection**

📦 **Product:** {name}
📏 **Size:** {size_display}
💰 **Price:** ${price} each

Select quantity to add to cart:
"""
    
    # Create quantity buttons (1-10)
    keyboard = []
    for i in range(1, 11, 2):  # 1,3,5,7,9 and 2,4,6,8,10
        row = []
        for j in range(2):
            qty = i + j
            if qty <= 10:
                total_price = price * qty
                button_text = f"{qty} (${total_price})"
                row.append(InlineKeyboardButton(
                    button_text,
                    callback_data=f"add_qty_{category}_{product_id}_{size}_{qty}"
                ))
        keyboard.append(row)
    
    keyboard.append([
        InlineKeyboardButton("🔙 Back to Product", callback_data=f"view_{category}_{product_id}"),
        InlineKeyboardButton("🛒 View Cart", callback_data="cart")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_admin_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin settings."""
    text = """
⚙️ **Admin Settings**

Bot configuration and management options.

Coming soon!
"""
    
    keyboard = [[InlineKeyboardButton("🏠 Back to Admin", callback_data="admin")]]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

# ========================
# ADVANCED COMBO SYSTEM
# ========================

async def handle_combo_action(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle combo-related actions."""
    user_id = update.effective_user.id
    
    if data == "combo_builder":
        await show_combo_builder_menu(update, context)
    elif data.startswith("combo_type_"):
        combo_type = data.replace("combo_type_", "")
        await start_combo_builder(update, context, combo_type)
    elif data.startswith("combo_add_"):
        await handle_combo_product_selection(update, context, data)
    elif data == "combo_finish":
        await finalize_combo(update, context)
    elif data == "combo_clear":
        await clear_combo_builder(update, context)
    elif data.startswith("combo_remove_"):
        await remove_from_combo(update, context, data)
    else:
        await update.callback_query.edit_message_text("❌ Unknown combo action.")

async def show_combo_builder_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show combo builder type selection."""
    text = """
🔥 **Combo Builder**

Create custom product combinations with special pricing!

Select combo type:
"""
    
    from config import COMBO_TYPES
    keyboard = []
    
    for combo_id, combo_config in COMBO_TYPES.items():
        name = combo_config['name']
        description = combo_config['description']
        button_text = f"{name} - {description}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"combo_type_{combo_id}")])
    
    keyboard.append([InlineKeyboardButton("🏠 Back to Menu", callback_data="menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def start_combo_builder(update: Update, context: ContextTypes.DEFAULT_TYPE, combo_type: str):
    """Start building a specific combo type."""
    from config import COMBO_TYPES
    
    combo_config = COMBO_TYPES.get(combo_type)
    if not combo_config:
        await update.callback_query.edit_message_text("❌ Invalid combo type.")
        return
    
    # Initialize combo session
    context.user_data['combo_builder'] = {
        'type': combo_type,
        'config': combo_config,
        'selected_products': [],
        'started_at': get_current_time().isoformat()
    }
    
    requirements = combo_config['requirements']
    required_quantity = requirements['quantity']
    required_size = requirements['size']
    star_restriction = requirements.get('star_restriction')
    
    text = f"""
🔥 **{combo_config['name']} Builder**

**Requirements:**
• Select exactly {required_quantity} products
• All products must have {required_size} size
"""
    
    if star_restriction:
        text += f"• {star_restriction} products not allowed\n"
    
    text += f"\n**Selected: 0/{required_quantity}**\n\nChoose products from our flower menu:"
    
    await show_combo_product_selection(update, context, text)

async def show_combo_product_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, header_text: str):
    """Show available products for combo selection."""
    combo_data = context.user_data.get('combo_builder', {})
    combo_config = combo_data.get('config', {})
    requirements = combo_config.get('requirements', {})
    
    required_size = requirements.get('size', 'eighth')
    star_restriction = requirements.get('star_restriction')
    
    # Get flower products
    products = data_manager.get_products_by_category('🌿 Flower')
    
    # Filter products that meet requirements
    available_products = {}
    for product_id, product in products.items():
        if not product.get('visible', True):
            continue
            
        # Check if product has required size
        if required_size not in product.get('prices', {}):
            continue
            
        # Check star restriction
        if star_restriction and product.get('grade') == star_restriction:
            continue
            
        available_products[product_id] = product
    
    if not available_products:
        text = header_text + "\n\n❌ No products available for this combo type."
        keyboard = [[InlineKeyboardButton("🏠 Back to Menu", callback_data="menu")]]
    else:
        text = header_text + "\n\n**Available Products:**"
        keyboard = []
        
        for product_id, product in available_products.items():
            name = product.get('name', 'Unknown')
            grade = product.get('grade', '⭐')
            price = product.get('prices', {}).get(required_size, 0)
            
            button_text = f"{name} {grade} - ${price}"
            keyboard.append([InlineKeyboardButton(
                button_text, 
                callback_data=f"combo_add_{product_id}"
            )])
        
        # Add control buttons
        selected_count = len(combo_data.get('selected_products', []))
        required_count = requirements.get('quantity', 2)
        
        if selected_count > 0:
            keyboard.append([InlineKeyboardButton("📋 Review Selection", callback_data="combo_review")])
            keyboard.append([InlineKeyboardButton("🗑️ Clear Selection", callback_data="combo_clear")])
        
        if selected_count == required_count:
            keyboard.append([InlineKeyboardButton("✅ Finish Combo", callback_data="combo_finish")])
    
    keyboard.append([InlineKeyboardButton("🏠 Back to Menu", callback_data="menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_combo_product_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle product selection for combo."""
    product_id = data.replace("combo_add_", "")
    combo_data = context.user_data.get('combo_builder', {})
    
    if not combo_data:
        await update.callback_query.edit_message_text("❌ No active combo session.")
        return
    
    combo_config = combo_data['config']
    requirements = combo_config['requirements']
    required_quantity = requirements['quantity']
    required_size = requirements['size']
    
    # Check if already at capacity
    selected_products = combo_data.get('selected_products', [])
    if len(selected_products) >= required_quantity:
        await update.callback_query.answer("❌ Maximum products selected for this combo!")
        return
    
    # Get product details
    product = data_manager.get_product('🌿 Flower', product_id)
    if not product:
        await update.callback_query.answer("❌ Product not found!")
        return
    
    # Check if product already selected
    if any(p['product_id'] == product_id for p in selected_products):
        await update.callback_query.answer("❌ Product already selected!")
        return
    
    # Add to selection
    price = product.get('prices', {}).get(required_size, 0)
    selected_product = {
        'product_id': product_id,
        'name': product.get('name'),
        'grade': product.get('grade'),
        'size': required_size,
        'price': price,
        'category': '🌿 Flower'
    }
    
    selected_products.append(selected_product)
    combo_data['selected_products'] = selected_products
    
    # Update header text
    header_text = f"""
🔥 **{combo_config['name']} Builder**

**Selected: {len(selected_products)}/{required_quantity}**
"""
    
    for i, sp in enumerate(selected_products):
        header_text += f"{i+1}. {sp['name']} {sp['grade']} - ${sp['price']}\n"
    
    await show_combo_product_selection(update, context, header_text)

async def finalize_combo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Finalize the combo and add to cart."""
    user_id = update.effective_user.id
    combo_data = context.user_data.get('combo_builder', {})
    
    if not combo_data:
        await update.callback_query.edit_message_text("❌ No active combo session.")
        return
    
    combo_config = combo_data['config']
    selected_products = combo_data.get('selected_products', [])
    requirements = combo_config['requirements']
    
    # Validate combo
    from utils import validate_combo_selection
    is_valid, error_message = validate_combo_selection(selected_products, combo_data['type'])
    
    if not is_valid:
        await update.callback_query.edit_message_text(f"❌ {error_message}")
        return
    
    # Calculate combo pricing
    individual_prices = [p['price'] for p in selected_products]
    combo_price = calculate_combo_price(individual_prices, combo_config['pricing_method'])
    
    # Calculate savings
    individual_total = sum(individual_prices)
    savings = individual_total - combo_price
    
    # Create combo item for cart
    combo_item = {
        'product_id': f"combo_{combo_data['type']}_{int(get_current_time().timestamp())}",
        'category': '🔥 Combos/Deals',
        'name': f"{combo_config['name']} - {', '.join(p['name'] for p in selected_products)}",
        'size': 'combo',
        'price': combo_price,
        'quantity': 1,
        'combo_type': combo_data['type'],
        'combo_products': selected_products,
        'individual_total': individual_total,
        'savings': savings
    }
    
    # Add to cart
    data_manager.add_to_cart(user_id, combo_item)
    
    # Clear combo session
    if 'combo_builder' in context.user_data:
        del context.user_data['combo_builder']
    
    # Show success message
    text = f"""
✅ **Combo Added to Cart!**

**{combo_config['name']}**
{', '.join(p['name'] + ' ' + p['grade'] for p in selected_products)}

**Individual Total:** ${individual_total}
**Combo Price:** ${combo_price}
**You Save:** ${savings}

What would you like to do next?
"""
    
    keyboard = [
        [InlineKeyboardButton("🛒 View Cart", callback_data="cart")],
        [InlineKeyboardButton("🔥 Build Another Combo", callback_data="combo_builder")],
        [InlineKeyboardButton("🛍️ Continue Shopping", callback_data="menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def clear_combo_builder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear combo builder session."""
    if 'combo_builder' in context.user_data:
        del context.user_data['combo_builder']
    
    await update.callback_query.edit_message_text(
        "🗑️ Combo selection cleared!\n\nReady to start fresh?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔥 Build Combo", callback_data="combo_builder")],
            [InlineKeyboardButton("🛍️ Browse Menu", callback_data="menu")]
        ])
    )

# ========================
# BUG FIX HANDLERS
# ========================

async def handle_notify_request(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle notification request for product category."""
    user_id = update.effective_user.id
    category = data.replace("notify_", "")
    
    # Add user to notification list for this category
    data_manager.add_notification_request(user_id, category)
    
    text = f"""
🔔 **Notification Set!**

You'll be notified when new products are added to **{category}**.

✅ **What happens next:**
• Get instant alerts for new arrivals
• Be first to know about restocks
• Receive special category announcements

You can manage your notifications in /notifications anytime.
"""
    
    keyboard = [
        [InlineKeyboardButton("🔔 Manage Notifications", callback_data="notifications")],
        [InlineKeyboardButton("🏠 Back to Menu", callback_data="menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_region_alert(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle region alert selection."""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.callback_query.answer("❌ Access denied.")
        return
    
    region_id = data.replace("alert_region_", "")
    region_data = REGIONS.get(region_id, {})
    region_name = region_data.get('name', region_id)
    
    text = f"""
📍 **Send Alert to {region_name}**

What type of alert would you like to send?
"""
    
    keyboard = [
        [InlineKeyboardButton("🆕 New Arrival Alert", callback_data=f"send_alert_arrival_{region_id}")],
        [InlineKeyboardButton("🔥 Fire Sale Alert", callback_data=f"send_alert_firesale_{region_id}")],
        [InlineKeyboardButton("📦 Restock Alert", callback_data=f"send_alert_restock_{region_id}")],
        [InlineKeyboardButton("📢 Custom Message", callback_data=f"send_alert_custom_{region_id}")],
        [InlineKeyboardButton("🏠 Back to Admin", callback_data="admin")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_send_alert(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle sending alerts to regions."""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.callback_query.answer("❌ Access denied.")
        return
    
    parts = data.split("_", 3)  # send_alert_type_region
    if len(parts) < 4:
        await update.callback_query.edit_message_text("❌ Invalid alert action.")
        return
    
    alert_type = parts[2]
    region_id = parts[3]
    region_data = REGIONS.get(region_id, {})
    region_name = region_data.get('name', region_id)
    
    # Get users in this region
    users_in_region = data_manager.get_users_by_region(region_id)
    
    if not users_in_region:
        await update.callback_query.edit_message_text(
            f"📍 No users found in {region_name}.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Back to Admin", callback_data="admin")]
            ])
        )
        return
    
    # Create alert message based on type
    if alert_type == "arrival":
        alert_text = f"🆕 **New Products Available in {region_name}!**\n\nCheck out our latest arrivals! Use /menu to browse."
    elif alert_type == "firesale":
        alert_text = f"🔥 **Fire Sale Active in {region_name}!**\n\nLimited time - special pricing on select items! Use /menu to shop now."
    elif alert_type == "restock":
        alert_text = f"📦 **Popular Items Restocked in {region_name}!**\n\nYour favorites are back! Use /menu to order."
    else:
        # Custom message - would need text input handling
        await update.callback_query.edit_message_text(
            "📝 Custom message alerts coming soon!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Back to Admin", callback_data="admin")]
            ])
        )
        return
    
    # Send alerts to users
    sent_count = 0
    for user_id_to_notify in users_in_region:
        try:
            if not data_manager.is_category_muted(user_id_to_notify, 'location_alerts'):
                await context.bot.send_message(
                    chat_id=user_id_to_notify,
                    text=alert_text,
                    parse_mode='Markdown'
                )
                sent_count += 1
        except Exception as e:
            logger.error(f"Failed to send alert to user {user_id_to_notify}: {e}")
    
    await update.callback_query.edit_message_text(
        f"✅ Alert sent to {sent_count} users in {region_name}!",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📍 Send Another Alert", callback_data="admin_region_alerts")],
            [InlineKeyboardButton("🏠 Back to Admin", callback_data="admin")]
        ])
    )

async def handle_add_quantity_to_cart(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle adding specific quantity to cart."""
    parts = data.split("_", 5)  # add_qty_category_productid_size_quantity
    if len(parts) != 6:
        await update.callback_query.edit_message_text("❌ Invalid quantity selection.")
        return
    
    user_id = update.effective_user.id
    category = parts[2]
    product_id = parts[3]
    size = parts[4]
    quantity = int(parts[5])
    
    product = data_manager.get_product(category, product_id)
    if not product:
        await update.callback_query.edit_message_text("❌ Product not found.")
        return
    
    price = product.get('prices', {}).get(size)
    if price is None:
        await update.callback_query.edit_message_text("❌ Size not available.")
        return
    
    # Apply fire sale discount if active
    if data_manager.is_fire_sale_active():
        from utils import calculate_fire_sale_price
        price = calculate_fire_sale_price(price)
    
    # Create cart item
    cart_item = {
        'product_id': product_id,
        'category': category,
        'name': product.get('name'),
        'grade': product.get('grade'),
        'size': size,
        'price': price,
        'quantity': quantity
    }
    
    # Add to cart
    data_manager.add_to_cart(user_id, cart_item)
    
    total_price = price * quantity
    from utils import get_size_display_name
    size_display = get_size_display_name(size)
    
    await update.callback_query.edit_message_text(
        f"✅ Added {quantity}x {product.get('name')} ({size_display}) to cart!\n\n💰 Total: ${total_price}\n\nWhat would you like to do next?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🛒 View Cart", callback_data="cart")],
            [InlineKeyboardButton("➕ Continue Shopping", callback_data="menu")],
            [InlineKeyboardButton("✅ Checkout", callback_data="checkout")]
        ])
    )

# ========================
# ADDITIONAL FIRE SALE HANDLERS
# ========================

async def handle_fire_sale_start_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle fire sale start confirmation."""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.callback_query.answer("❌ Access denied.")
        return
    
    # Start fire sale for 4 hours by default
    success = data_manager.start_fire_sale([], 25, 4, user_id)
    
    if success:
        # Notify all users about fire sale
        users_to_notify = data_manager.get_notification_recipients('fire_sales')
        
        fire_sale_text = """
🔥 **FIRE SALE NOW ACTIVE!** 🔥

💥 **25% OFF ALL PRODUCTS** 💥

Limited time only! Shop now before it ends!

Use /menu to browse and save big!
"""
        
        sent_count = 0
        for notify_user_id in users_to_notify:
            try:
                await context.bot.send_message(
                    chat_id=notify_user_id,
                    text=fire_sale_text,
                    parse_mode='Markdown'
                )
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to notify user {notify_user_id}: {e}")
        
        await update.callback_query.edit_message_text(
            f"🔥 **Fire Sale Started!**\n\n✅ 25% discount activated\n📢 Notified {sent_count} users\n⏰ Duration: 4 hours",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔥 Manage Fire Sale", callback_data="admin_fire_sale")],
                [InlineKeyboardButton("🏠 Back to Admin", callback_data="admin")]
            ])
        )
    else:
        await update.callback_query.edit_message_text(
            "❌ Failed to start fire sale.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Back to Admin", callback_data="admin")]
            ])
        )

async def handle_fire_sale_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle fire sale scheduling."""
    await update.callback_query.edit_message_text(
        "⏰ **Schedule Fire Sale**\n\nScheduled fire sales coming soon!\n\nFor now, you can start immediate fire sales.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔥 Start Now Instead", callback_data="fire_start_confirm")],
            [InlineKeyboardButton("🏠 Back to Admin", callback_data="admin")]
        ])
    )

async def handle_fire_sale_targeted(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle targeted fire sale."""
    await update.callback_query.edit_message_text(
        "🎯 **Targeted Fire Sale**\n\nRegion-specific fire sales coming soon!\n\nFor now, fire sales apply to all regions.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔥 Start Global Fire Sale", callback_data="fire_start_confirm")],
            [InlineKeyboardButton("🏠 Back to Admin", callback_data="admin")]
        ])
    )

async def handle_fire_sale_preview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle fire sale preview."""
    # Calculate potential impact
    total_products = sum(len(products) for products in data_manager.fallback_products.values())
    total_users = len(data_manager.user_regions)
    active_carts = len([cart for cart in data_manager.user_cart.values() if cart])
    
    estimated_sales_boost = total_users * 0.3  # Estimate 30% of users will purchase
    estimated_revenue = estimated_sales_boost * 75  # Average $75 per order
    
    text = f"""
📊 **Fire Sale Impact Preview**

🔥 **25% Discount Analysis:**

📦 **Products Affected:** {total_products} items
👥 **Potential Customers:** {total_users} users
🛒 **Active Shoppers:** {active_carts} with items in cart

💰 **Estimated Impact:**
• Expected orders: ~{estimated_sales_boost:.0f}
• Projected revenue: ~${estimated_revenue:,.0f}
• Discount cost: ~${estimated_revenue * 0.25:,.0f}
• Net revenue: ~${estimated_revenue * 0.75:,.0f}

⚡ **Urgency Factor:** Fire sales typically drive 40-60% immediate conversions

**Ready to launch?**
"""
    
    keyboard = [
        [InlineKeyboardButton("🔥 Launch Fire Sale Now", callback_data="fire_start_confirm")],
        [InlineKeyboardButton("📊 View Detailed Analytics", callback_data="admin_stats")],
        [InlineKeyboardButton("🏠 Back to Admin", callback_data="admin")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

# ========================
# HIGH PRIORITY IMPLEMENTATIONS
# ========================

async def handle_region_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle broadcasting to all regions with real data integration."""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.callback_query.answer("❌ Access denied.")
        return
    
    # Real data from data_manager
    total_users = len(data_manager.user_regions)
    region_breakdown = {}
    
    for uid, region in data_manager.user_regions.items():
        region_breakdown[region] = region_breakdown.get(region, 0) + 1
    
    # Calculate actual notification reach
    active_notification_users = 0
    for uid in data_manager.user_regions.keys():
        if not data_manager.is_category_muted(uid, 'location_alerts'):
            active_notification_users += 1
    
    text = f"""
📢 **Broadcast to All Regions**

📊 **Real-Time Reach Analysis:**
• Total registered users: **{total_users}**
• Will receive notification: **{active_notification_users}**
• Muted users: **{total_users - active_notification_users}**
• Delivery coverage: **{len(REGIONS)} regions**

📍 **Current Regional Distribution:**
"""
    
    for region_id, count in region_breakdown.items():
        region_name = REGIONS.get(region_id, {}).get('name', region_id)
        percentage = (count / max(total_users, 1)) * 100
        active_in_region = len([u for u in data_manager.get_users_by_region(region_id) 
                               if not data_manager.is_category_muted(u, 'location_alerts')])
        text += f"• {region_name}: **{count}** users ({active_in_region} active, {percentage:.1f}%)\n"
    
    text += """

🎯 **Broadcast Message Types:**
Choose the type of message to send to all regions:
"""
    
    keyboard = [
        [InlineKeyboardButton("🆕 New Product Launch", callback_data="broadcast_new_product")],
        [InlineKeyboardButton("🔥 Flash Sale Alert", callback_data="broadcast_flash_sale")],
        [InlineKeyboardButton("📦 Inventory Update", callback_data="broadcast_inventory")],
        [InlineKeyboardButton("🚛 Service Update", callback_data="broadcast_service")],
        [InlineKeyboardButton("📝 Custom Message", callback_data="broadcast_custom")],
        [InlineKeyboardButton("🏠 Back to Region Alerts", callback_data="admin_region_alerts")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_alert_analytics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle alert analytics with comprehensive real data."""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.callback_query.answer("❌ Access denied.")
        return
    
    # Real analytics data from data_manager
    total_users = len(data_manager.user_regions)
    
    # Notification preferences analysis
    notification_stats = {
        'total_muted': 0,
        'category_mutes': {},
        'active_requests': 0
    }
    
    for uid in data_manager.user_regions.keys():
        settings = data_manager.get_user_notification_settings(uid)
        muted_cats = settings.get('muted_categories', {})
        
        if muted_cats:
            notification_stats['total_muted'] += 1
            
        for cat in muted_cats:
            notification_stats['category_mutes'][cat] = notification_stats['category_mutes'].get(cat, 0) + 1
        
        if settings.get('category_requests'):
            notification_stats['active_requests'] += 1
    
    # Regional engagement calculation
    region_engagement = {}
    for region_id in REGIONS.keys():
        users_in_region = data_manager.get_users_by_region(region_id)
        active_in_region = len([u for u in users_in_region if not data_manager.is_category_muted(u, 'location_alerts')])
        if users_in_region:
            engagement_rate = (active_in_region / len(users_in_region)) * 100
            region_engagement[region_id] = {
                'total': len(users_in_region),
                'active': active_in_region,
                'rate': engagement_rate
            }
    
    # Category-specific reach
    category_reach = {}
    for category in NOTIFICATION_CATEGORIES:
        reach = len([u for u in data_manager.user_regions.keys() 
                    if not data_manager.is_category_muted(u, category)])
        category_reach[category] = reach
    
    text = f"""
📊 **Alert Analytics Dashboard**

🕒 **Real-Time Data:** {get_current_time().strftime('%I:%M %p')}

👥 **USER ENGAGEMENT METRICS**
• Total Users: **{total_users}**
• Active Notifications: **{total_users - notification_stats['total_muted']}**
• Users with Muted Categories: **{notification_stats['total_muted']}**
• Pending Notification Requests: **{notification_stats['active_requests']}**

📱 **CATEGORY REACH ANALYSIS**
• Location Alerts: **{category_reach.get('location_alerts', 0)}** users
• Fire Sale Alerts: **{category_reach.get('fire_sales', 0)}** users
• New Arrivals: **{category_reach.get('new_arrivals', 0)}** users
• Order Updates: **{category_reach.get('order_updates', 0)}** users

🌍 **REGIONAL ENGAGEMENT**
"""
    
    for region_id, stats in region_engagement.items():
        region_name = REGIONS.get(region_id, {}).get('name', region_id)
        text += f"• {region_name}: **{stats['active']}/{stats['total']}** active ({stats['rate']:.1f}%)\n"
    
    avg_engagement = sum(s['rate'] for s in region_engagement.values()) / max(len(region_engagement), 1)
    best_region = max(region_engagement.items(), key=lambda x: x[1]['rate'])[0] if region_engagement else 'N/A'
    best_region_name = REGIONS.get(best_region, {}).get('name', best_region)
    
    text += f"""

📈 **PERFORMANCE INSIGHTS**
• Average Engagement Rate: **{avg_engagement:.1f}%**
• Best Performing Region: **{best_region_name}** ({region_engagement.get(best_region, {}).get('rate', 0):.1f}%)
• Overall Notification Health: **{'Excellent' if avg_engagement > 80 else 'Good' if avg_engagement > 60 else 'Needs Attention'}**

🎯 **ACTIONABLE RECOMMENDATIONS**
"""
    
    # Smart recommendations based on real data
    if notification_stats['total_muted'] > total_users * 0.3:
        text += "• **Reduce frequency** - High mute rate detected\n"
    if notification_stats['active_requests'] > 0:
        text += f"• **{notification_stats['active_requests']} users** waiting for product notifications\n"
    if min([s['rate'] for s in region_engagement.values()], default=100) < 50:
        text += "• **Re-engage low-activity regions** with targeted content\n"
    if avg_engagement > 80:
        text += "• **Excellent engagement** - Consider increasing alert frequency\n"
    
    keyboard = [
        [InlineKeyboardButton("📊 Export Analytics", callback_data="export_analytics")],
        [InlineKeyboardButton("🎯 Optimize Campaigns", callback_data="optimize_campaigns")],
        [InlineKeyboardButton("📱 Test Notification", callback_data="test_notification")],
        [InlineKeyboardButton("🔄 Refresh Data", callback_data="alert_analytics")],
        [InlineKeyboardButton("🏠 Back to Region Alerts", callback_data="admin_region_alerts")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_custom_regional_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle custom regional messaging with real user data."""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.callback_query.answer("❌ Access denied.")
        return
    
    # Real user distribution from data_manager
    region_breakdown = {}
    for uid, region in data_manager.user_regions.items():
        region_breakdown[region] = region_breakdown.get(region, 0) + 1
    
    total_users = len(data_manager.user_regions)
    
    text = f"""
📝 **Custom Regional Message Creator**

🎯 **Real-Time Targeting Data:**

📊 **Available Audiences:**
• All Regions: **{total_users}** users
"""
    
    for region_id, count in region_breakdown.items():
        region_name = REGIONS.get(region_id, {}).get('name', region_id)
        active_count = len([u for u in data_manager.get_users_by_region(region_id) 
                           if not data_manager.is_category_muted(u, 'location_alerts')])
        text += f"• {region_name}: **{count}** users ({active_count} will receive alerts)\n"
    
    text += """

💡 **Message Templates:**
Pre-built templates for common announcements:
"""
    
    keyboard = [
        [InlineKeyboardButton("📦 Product Announcement", callback_data="template_product")],
        [InlineKeyboardButton("🚛 Delivery Update", callback_data="template_delivery")],
        [InlineKeyboardButton("🎉 Special Event", callback_data="template_event")],
        [InlineKeyboardButton("⚠️ Important Notice", callback_data="template_notice")],
        [InlineKeyboardButton("✏️ Write Custom Message", callback_data="custom_message_input")],
        [InlineKeyboardButton("🏠 Back to Region Alerts", callback_data="admin_region_alerts")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_admin_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle comprehensive admin statistics with full data integration."""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.callback_query.answer("❌ Access denied.")
        return
    
    # Complete real data integration from data_manager
    total_users = len(data_manager.user_regions)
    
    # Real order statistics
    all_orders = []
    for user_orders in data_manager.user_orders.values():
        all_orders.extend(user_orders)
    
    total_orders = len(all_orders)
    pending_orders = len([o for o in all_orders if o.get('status') == 'pending'])
    approved_orders = len([o for o in all_orders if o.get('status') == 'approved'])
    completed_orders = len([o for o in all_orders if o.get('status') in ['delivered', 'completed']])
    
    # Real revenue calculations
    total_revenue = sum(o.get('total_price', 0) for o in all_orders if o.get('status') in ['delivered', 'completed', 'approved'])
    pending_revenue = sum(o.get('total_price', 0) for o in all_orders if o.get('status') == 'pending')
    average_order_value = total_revenue / max(completed_orders, 1)
    
    # Real product inventory
    total_products = sum(len(products) for products in data_manager.fallback_products.values())
    visible_products = 0
    
    for category, products in data_manager.fallback_products.items():
        for product in products.values():
            if product.get('visible', True):
                visible_products += 1
    
    # Real user engagement
    active_carts = len([cart for cart in data_manager.user_cart.values() if cart])
    total_cart_items = sum(len(cart) for cart in data_manager.user_cart.values())
    
    # Fire sale status
    fire_sale_active = data_manager.is_fire_sale_active()
    fire_sale_status = "🔥 ACTIVE" if fire_sale_active else "⏸️ Inactive"
    
    text = f"""
📈 **Comprehensive Analytics Dashboard**

🕒 **Live Data:** {get_current_time().strftime('%B %d, %Y at %I:%M %p')}

👥 **USER METRICS**
• Total Registered: **{total_users}**
• Active Carts: **{active_carts}** ({(active_carts/max(total_users,1)*100):.1f}%)
• Cart Items: **{total_cart_items}**

📦 **ORDER ANALYTICS**
• Total Orders: **{total_orders}**
• Pending: **{pending_orders}** ⚠️
• Approved: **{approved_orders}** ✅
• Completed: **{completed_orders}** 📦

💰 **REVENUE INTELLIGENCE**
• Total Revenue: **${total_revenue:,.2f}**
• Pending Value: **${pending_revenue:,.2f}**
• Average Order: **${average_order_value:.2f}**

🌿 **INVENTORY STATUS**
• Total Products: **{total_products}**
• Visible: **{visible_products}**

🔥 **SYSTEM STATUS**
• Fire Sale: {fire_sale_status}
• Bot Health: 🟢 Optimal
• Data Sync: ✅ Real-time
"""
    
    keyboard = [
        [InlineKeyboardButton("💰 Revenue Deep Dive", callback_data="admin_revenue_deep")],
        [InlineKeyboardButton("👥 User Behavior", callback_data="admin_user_behavior")],
        [InlineKeyboardButton("📦 Order Analytics", callback_data="admin_order_analytics")],
        [InlineKeyboardButton("🔄 Refresh All Data", callback_data="admin_detailed_stats")],
        [InlineKeyboardButton("🏠 Back to Admin", callback_data="admin")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_fire_sale_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle fire sale toggle with comprehensive data integration."""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.callback_query.answer("❌ Access denied.")
        return
    
    # Real-time fire sale status from data_manager
    current_status = data_manager.is_fire_sale_active()
    
    if current_status:
        # Fire sale is ACTIVE
        fire_sale_data = data_manager.get_fire_sale_data()
        duration = fire_sale_data.get('duration_hours', 0)
        
        # Real impact metrics
        total_products = sum(len(products) for products in data_manager.fallback_products.values())
        current_active_carts = len([cart for cart in data_manager.user_cart.values() if cart])
        current_pending_orders = len([o for o in sum(data_manager.user_orders.values(), []) 
                                     if o.get('status') == 'pending'])
        
        text = f"""
🔥 **FIRE SALE ACTIVE** 🔥

📊 **Current Status:**
• Discount Rate: **25% OFF ALL PRODUCTS**
• Duration: **{duration} hours**

📈 **Live Performance:**
• Products on Sale: **{total_products}** items
• Active Shoppers: **{current_active_carts}**
• Pending Orders: **{current_pending_orders}**

**🔥 Fire Sale Management:**
"""
        
        keyboard = [
            [InlineKeyboardButton("⏹️ End Fire Sale Now", callback_data="fire_end_confirm")],
            [InlineKeyboardButton("📊 View Performance", callback_data="fire_performance")],
            [InlineKeyboardButton("🏠 Back to Admin", callback_data="admin")]
        ]
    
    else:
        # Fire sale is INACTIVE
        total_products = sum(len(products) for products in data_manager.fallback_products.values())
        total_users = len(data_manager.user_regions)
        active_carts = len([cart for cart in data_manager.user_cart.values() if cart])
        
        text = f"""
⏸️ **Fire Sale Launch Control**

🎯 **Market Readiness:**
• Total Products: **{total_products}** items ready
• Registered Users: **{total_users}**
• Active Shoppers: **{active_carts}** with cart items

⚡ **Launch Options:**
"""
        
        keyboard = [
            [InlineKeyboardButton("🔥 Start 4-Hour Fire Sale", callback_data="fire_start_4h")],
            [InlineKeyboardButton("🔥 Start 8-Hour Fire Sale", callback_data="fire_start_8h")],
            [InlineKeyboardButton("📊 Preview Impact", callback_data="fire_preview")],
            [InlineKeyboardButton("🏠 Back to Admin", callback_data="admin")]
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_fire_start_duration(update: Update, context: ContextTypes.DEFAULT_TYPE, duration_hours: int):
    """Handle starting fire sale with specific duration."""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.callback_query.answer("❌ Access denied.")
        return
    
    # Start fire sale with specified duration
    success = data_manager.start_fire_sale([], 25, duration_hours, user_id)
    
    if success:
        # Notify all users about fire sale
        users_to_notify = data_manager.get_notification_recipients('fire_sales')
        
        fire_sale_text = f"""
🔥 **FIRE SALE NOW ACTIVE!** 🔥

💥 **25% OFF ALL PRODUCTS** 💥

⏰ **Limited Time: {duration_hours} Hours Only!**

Shop now before it ends!

Use /menu to browse and save big!
"""
        
        sent_count = 0
        for notify_user_id in users_to_notify:
            try:
                await context.bot.send_message(
                    chat_id=notify_user_id,
                    text=fire_sale_text,
                    parse_mode='Markdown'
                )
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to notify user {notify_user_id}: {e}")
        
        await update.callback_query.edit_message_text(
            f"🔥 **Fire Sale Started!**\n\n✅ 25% discount activated for {duration_hours} hours\n📢 Notified {sent_count} users\n🚀 Launch successful!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔥 Manage Fire Sale", callback_data="fire_toggle")],
                [InlineKeyboardButton("📊 View Performance", callback_data="admin_detailed_stats")],
                [InlineKeyboardButton("🏠 Back to Admin", callback_data="admin")]
            ])
        )
    else:
        await update.callback_query.edit_message_text(
            "❌ Failed to start fire sale. Please try again.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Try Again", callback_data="fire_toggle")],
                [InlineKeyboardButton("🏠 Back to Admin", callback_data="admin")]
            ])
        )

async def handle_fire_end(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle ending fire sale."""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.callback_query.answer("❌ Access denied.")
        return
    
    # End fire sale
    success = data_manager.end_fire_sale()
    
    if success:
        # Get some final stats
        total_users = len(data_manager.user_regions)
        active_carts = len([cart for cart in data_manager.user_cart.values() if cart])
        
        await update.callback_query.edit_message_text(
            f"✅ **Fire Sale Ended Successfully**\n\n🔥 Sale concluded\n💰 Pricing returned to normal\n📊 Final stats: {active_carts} active carts from {total_users} users\n\nThank you for using the fire sale system!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📊 View Final Report", callback_data="admin_detailed_stats")],
                [InlineKeyboardButton("🔥 Plan Next Fire Sale", callback_data="fire_toggle")],
                [InlineKeyboardButton("🏠 Back to Admin", callback_data="admin")]
            ])
        )
    else:
        await update.callback_query.edit_message_text(
            "❌ Failed to end fire sale. It may already be ended.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Refresh Status", callback_data="fire_toggle")],
                [InlineKeyboardButton("🏠 Back to Admin", callback_data="admin")]
            ])
        )

async def handle_region_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle region confirmation after user selects from sub-areas."""
    user_id = update.effective_user.id
    region_id = data.replace("confirm_region_", "")
    
    # Save user's region
    data_manager.set_user_region(user_id, region_id)
    
    region_name = REGIONS.get(region_id, {}).get('name', region_id)
    
    await update.callback_query.edit_message_text(
        f"✅ **Region Confirmed!**\n\n📍 You're now set for: **{region_name}**\n\n🔔 You'll receive alerts for this region\n\nRedirecting to menu...",
        parse_mode='Markdown'
    )
    
    # Show main menu after setting region
    from handlers.command_handlers import show_main_menu
    await show_main_menu(update, context, region_id)

async def handle_back_to_regions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle back to region selection."""
    from handlers.command_handlers import show_region_selection
    await show_region_selection(update, context)