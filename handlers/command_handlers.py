import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from data_manager import data_manager
from utils import is_admin, get_current_time
from config import REGIONS, PRODUCT_CATEGORIES

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    user = update.effective_user
    logger.info(f"User {user.id} ({user.username}) started the bot")
    
    welcome_text = f"""
🌿 Welcome to TTK Cannabis Delivery! 🌿

Hello {user.first_name}! I'm your personal cannabis delivery assistant.

Here's what I can help you with:
• 📱 Browse our premium product catalog
• 🛒 Manage your shopping cart
• 📍 Track delivery locations
• 🔔 Get notifications about deals and arrivals

To get started, use /menu to browse our products or /help for more commands.

⚠️ Must be 21+ to use this service
🚗 Delivery available in Philadelphia & Jersey areas
"""
    
    # Create inline keyboard for quick actions
    keyboard = [
        [InlineKeyboardButton("🛍️ Browse Menu", callback_data="menu")],
        [InlineKeyboardButton("🛒 View Cart", callback_data="cart")],
        [InlineKeyboardButton("📍 Saved Addresses", callback_data="saved_addresses")],
        [InlineKeyboardButton("🔔 Notifications", callback_data="notifications")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /menu command - main product browsing."""
    user_id = update.effective_user.id
    
    # Check if user has selected a region
    user_region = data_manager.get_user_region(user_id)
    
    if not user_region:
        await show_region_selection(update, context)
        return
    
    # Show main menu
    await show_main_menu(update, context, user_region)

async def show_region_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show region selection interface."""
    text = """
📍 **Select Your Region**

Please choose your delivery region to continue:
"""
    
    # Create region selection keyboard
    keyboard = []
    for region_id, region_data in REGIONS.items():
        keyboard.append([InlineKeyboardButton(
            region_data['name'], 
            callback_data=f"select_region_{region_id}"
        )])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, user_region: str):
    """Show the main product menu."""
    region_name = REGIONS.get(user_region, {}).get('name', user_region)
    
    text = f"""
🌿 **TTK Cannabis Delivery Menu** 🌿

📍 **Current Region:** {region_name}
🕒 **Last Updated:** {get_current_time().strftime('%I:%M %p')}

Select a category to browse our premium products:
"""
    
    # Create category selection keyboard
    keyboard = []
    for category in PRODUCT_CATEGORIES:
        if category != '👻 Hidden Menu':  # Hidden menu requires special access
            keyboard.append([InlineKeyboardButton(category, callback_data=f"category_{category}")])
    
    # Add special buttons
    keyboard.extend([
        [InlineKeyboardButton("🛒 View Cart", callback_data="cart")],
        [InlineKeyboardButton("📍 Change Region", callback_data="change_region")],
        [InlineKeyboardButton("🔔 Notifications", callback_data="notifications")]
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /cart command with advanced cart interface and real-time calculations."""
    user_id = update.effective_user.id
    cart_items = data_manager.get_user_cart(user_id)
    
    if not cart_items:
        text = """
🛒 **Your Cart is Empty**

Ready to discover premium cannabis products?

💡 **Suggestions:**
• Browse our top-rated flower strains
• Check out today's combo deals
• Explore new concentrates and edibles

Start your shopping journey below!
"""
        keyboard = [
            [InlineKeyboardButton("🌟 Featured Products", callback_data="featured")],
            [InlineKeyboardButton("🔥 Combo Deals", callback_data="category_🔥 Combos/Deals")],
            [InlineKeyboardButton("🛍️ Browse All Categories", callback_data="menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.message:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        return
    
    # Advanced cart calculations
    subtotal = 0
    fire_sale_savings = 0
    item_count = len(cart_items)
    total_quantity = sum(item.get('quantity', 1) for item in cart_items)
    
    # Check for combo eligibility
    flower_items = [item for item in cart_items if item.get('category') == '🌿 Flower']
    combo_eligible = len(flower_items) >= 2
    combo_savings = 0
    
    if combo_eligible:
        combo_total = sum(item.get('price', 0) * item.get('quantity', 1) for item in flower_items)
        from utils import calculate_combo_price
        combo_price, combo_savings = calculate_combo_price([item.get('price', 0) * item.get('quantity', 1) for item in flower_items])
    
    # Enhanced cart display with visual improvements
    text = f"""
🛒 **Your Shopping Cart**

📦 **{item_count} item{'s' if item_count != 1 else ''} ({total_quantity} total units)**

"""
    
    # Display each item with enhanced formatting
    for i, item in enumerate(cart_items):
        item_name = item.get('name', 'Unknown Product')
        quantity = item.get('quantity', 1)
        price = item.get('price', 0)
        size = item.get('size', '')
        grade = item.get('grade', '')
        category = item.get('category', '')
        
        # Apply fire sale discount if active
        original_price = price
        if data_manager.is_fire_sale_active():
            from utils import calculate_fire_sale_price
            price = calculate_fire_sale_price(price)
            fire_sale_savings += (original_price - price) * quantity
        
        item_total = price * quantity
        subtotal += item_total
        
        # Format size display
        from utils import get_size_display_name
        size_display = get_size_display_name(size) if size else ''
        
        # Item display with better formatting
        text += f"**{i+1}.** {item_name} {grade}\n"
        text += f"    📏 Size: {size_display}"
        
        if data_manager.is_fire_sale_active() and original_price != price:
            text += f"\n    💰 ~~${original_price}~~ **${price}** × {quantity} = **${item_total}**"
        else:
            text += f"\n    💰 ${price} × {quantity} = **${item_total}**"
        
        text += f"\n    🔧 [➖](callback_data=decrease_qty_{i}) **{quantity}** [➕](callback_data=increase_qty_{i}) | [🗑️](callback_data=remove_item_{i})\n\n"
    
    # Pricing breakdown
    text += "💳 **Pricing Breakdown:**\n"
    text += f"• Subtotal: **${subtotal}**\n"
    
    if fire_sale_savings > 0:
        text += f"• 🔥 Fire Sale Savings: **-${fire_sale_savings}**\n"
    
    if combo_eligible and combo_savings > 0:
        text += f"• 🎯 Combo Discount Available: **-${combo_savings}**\n"
        text += f"  *(Apply flower combo at checkout)*\n"
    
    # Calculate delivery fee
    user_region = data_manager.get_user_region(user_id)
    from config import REGIONS
    delivery_fee = REGIONS.get(user_region, {}).get('delivery_fee', 10)
    min_order = REGIONS.get(user_region, {}).get('min_order', 50)
    
    total_after_discounts = subtotal - fire_sale_savings
    if combo_eligible:
        total_after_discounts -= combo_savings
    
    text += f"• Delivery Fee: **${delivery_fee}**\n"
    
    final_total = total_after_discounts + delivery_fee
    text += f"\n💰 **Final Total: ${final_total}**"
    
    # Minimum order check
    if total_after_discounts < min_order:
        shortage = min_order - total_after_discounts
        text += f"\n⚠️ **Add ${shortage} more for delivery** (Min: ${min_order})"
    
    # Advanced cart action buttons with quantity controls
    keyboard = []
    
    # Individual item controls (show first 3 items for space)
    for i, item in enumerate(cart_items[:3]):
        item_name = item.get('name', 'Unknown Product')
        display_name = item_name[:15] + "..." if len(item_name) > 15 else item_name
        quantity = item.get('quantity', 1)
        
        qty_row = [
            InlineKeyboardButton(f"➖", callback_data=f"decrease_qty_{i}"),
            InlineKeyboardButton(f"{display_name} ({quantity})", callback_data=f"item_details_{i}"),
            InlineKeyboardButton(f"➕", callback_data=f"increase_qty_{i}")
        ]
        keyboard.append(qty_row)
    
    if len(cart_items) > 3:
        keyboard.append([InlineKeyboardButton("📋 Manage All Items", callback_data="manage_cart")])
    
    # Combo actions
    if combo_eligible:
        keyboard.append([InlineKeyboardButton("🎯 Apply Flower Combo", callback_data="apply_combo")])
    
    # Main actions
    main_actions = []
    if total_after_discounts >= min_order:
        main_actions.append(InlineKeyboardButton("✅ Proceed to Checkout", callback_data="checkout"))
    else:
        main_actions.append(InlineKeyboardButton("🛍️ Add More Items", callback_data="menu"))
    
    keyboard.append(main_actions)
    
    # Secondary actions
    keyboard.extend([
        [InlineKeyboardButton("💾 Save Cart", callback_data="save_cart"),
         InlineKeyboardButton("🔄 Quick Reorder", callback_data="quick_reorder")],
        [InlineKeyboardButton("🗑️ Clear Cart", callback_data="clear_cart"),
         InlineKeyboardButton("➕ Continue Shopping", callback_data="menu")]
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /admin command - admin control panel."""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Access denied. Admin privileges required.")
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
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /notifications command with enhanced mute interface and visualization."""
    user_id = update.effective_user.id
    settings = data_manager.get_user_notification_settings(user_id)
    
    # Enhanced notification status display
    muted_categories = settings.get('muted_categories', {})
    global_mute = settings.get('global_mute', False)
    
    if global_mute:
        status_text = "🔇 **All notifications are currently muted**"
        status_icon = "🔇"
    elif muted_categories:
        active_mutes = len(muted_categories)
        status_text = f"🔕 **{active_mutes} notification type{'s' if active_mutes != 1 else ''} muted**"
        status_icon = "🔕"
    else:
        status_text = "🔔 **All notifications are active**"
        status_icon = "🔔"
    
    text = f"""
{status_icon} **Notification Management**

{status_text}

📱 **Available Notification Types:**
• 🆕 New product arrivals
• 💰 Price drops & sales alerts  
• 🔥 Fire sale notifications
• 🎯 Combo deal alerts
• 📦 Order status updates
• 🚛 Delivery notifications

"""
    
    # Show detailed mute status with time remaining
    if muted_categories:
        text += "**🔇 Currently Muted Categories:**\n"
        from datetime import datetime
        current_time = datetime.now()
        
        for category, mute_data in muted_categories.items():
            # Calculate time remaining
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
                text += f"• 🔕 {category_display}: {time_text} remaining\n"
            else:
                # Mute expired, remove it
                data_manager.remove_user_mute(user_id, category)
        
        text += "\n"
    
    text += """**🎛️ Quick Actions:**
Choose how you'd like to manage your notifications:
"""
    
    # Enhanced notification control buttons
    keyboard = []
    
    if not global_mute:
        keyboard.extend([
            [InlineKeyboardButton("🔇 Mute by Category", callback_data="mute_categories"),
             InlineKeyboardButton("⏰ Quick Mute (3 days)", callback_data="quick_mute_3")],
            [InlineKeyboardButton("🔕 Mute All (1 week)", callback_data="mute_all_7"),
             InlineKeyboardButton("⏸️ Pause All (24h)", callback_data="mute_all_1")]
        ])
    else:
        keyboard.append([InlineKeyboardButton("🔊 Unmute All Notifications", callback_data="unmute_all")])
    
    if muted_categories:
        keyboard.append([InlineKeyboardButton("🔧 Manage Individual Mutes", callback_data="manage_mutes")])
    
    # Post-order mute suggestion (if user has recent orders)
    recent_orders = data_manager.get_user_orders(user_id)
    if recent_orders:
        last_order_time = recent_orders[-1].get('created_at', '')
        if last_order_time:
            from datetime import datetime, timedelta
            try:
                order_time = datetime.fromisoformat(last_order_time)
                if datetime.now() - order_time < timedelta(hours=24):
                    keyboard.append([InlineKeyboardButton("💡 Post-Order Mute (7 days)", callback_data="post_order_mute")])
            except:
                pass
    
    keyboard.extend([
        [InlineKeyboardButton("📊 Notification History", callback_data="notification_history"),
         InlineKeyboardButton("⚙️ Advanced Settings", callback_data="notification_advanced")],
        [InlineKeyboardButton("🏠 Back to Menu", callback_data="menu")]
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def addproduct(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /addproduct command - admin product creation."""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Access denied. Admin privileges required.")
        return
    
    # Set user state for product creation
    context.user_data['creating_product'] = True
    context.user_data['product_data'] = {}
    
    await update.message.reply_text("""
📷 **Add New Product**

Please send a photo or video of the product to get started.

You can send multiple media files and I'll let you choose which one to use.
""")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    text = """
🆘 **Help & Commands**

**Customer Commands:**
• /start - Welcome message and quick setup
• /menu - Browse product catalog
• /cart - View and manage your cart
• /notifications - Manage notification settings

**How to Order:**
1. Use /menu to browse products
2. Add items to your cart
3. Go to /cart and checkout
4. Wait for admin confirmation
5. Enjoy your delivery! 🌿

**Admin Commands:**
• /admin - Access admin control panel
• /addproduct - Add new products to catalog

**Need Help?**
Contact our support team through this bot for assistance.

⚠️ **Important:** Must be 21+ to use this service
🚗 Delivery available in Philadelphia & Jersey areas
"""
    
    await update.message.reply_text(text, parse_mode='Markdown')
