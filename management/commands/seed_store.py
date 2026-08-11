# management/commands/seed_store.py
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from api.models import ProductCategory, Product
import random

class Command(BaseCommand):
    help = 'Seed store with sample products'

    def handle(self, *args, **kwargs):
        self.stdout.write("🌱 Starting store seeding...")
        
        # Create or update categories
        categories = self.create_categories()
        
        # Create products
        self.create_products(categories)
        
        self.stdout.write(self.style.SUCCESS("✅ Store seeded successfully!"))
    
    def create_categories(self):
        """Create product categories"""
        categories = {}
        
        category_data = [
            {
                'name': 'Science Fair Kits',
                'slug': 'science-kits',
                'icon': '🔬',
                'description': 'Hands-on science experiment kits for school projects and science fairs',
                'order': 1
            },
            {
                'name': 'Electronics Components',
                'slug': 'electronics',
                'icon': '⚡',
                'description': 'Arduino, sensors, electronic components, and IoT devices',
                'order': 2
            },
            {
                'name': 'Readathon Books',
                'slug': 'readathon-books',
                'icon': '📚',
                'description': 'Curated books from the E-Readathon library for young readers',
                'order': 3
            },
            {
                'name': 'Robotics Kits',
                'slug': 'robotics',
                'icon': '🤖',
                'description': 'Build and code robots for competitions and learning',
                'order': 4
            },
            {
                'name': 'STEM Kits',
                'slug': 'stem-kits',
                'icon': '🧪',
                'description': 'Comprehensive STEM learning kits for all ages',
                'order': 5
            },
            {
                'name': 'Merchandise',
                'slug': 'merchandise',
                'icon': '👕',
                'description': 'Efunza branded merchandise and apparel',
                'order': 6
            },
            {
                'name': 'Digital Products',
                'slug': 'digital',
                'icon': '💻',
                'description': 'Digital downloads, e-books, and online resources',
                'order': 7
            },
        ]
        
        for data in category_data:
            category, created = ProductCategory.objects.get_or_create(
                slug=data['slug'],
                defaults=data
            )
            categories[data['slug']] = category
            
            if created:
                self.stdout.write(f"  ✅ Created category: {category.name}")
            else:
                self.stdout.write(f"  ↻ Updated category: {category.name}")
        
        return categories
    
    def create_products(self, categories):
        """Create sample products"""
        
        products = [
            # ============================================================
            # SCIENCE KITS
            # ============================================================
            {
                'name': 'Smart Farm Automation Kit',
                'description': 'Learn about IoT and smart farming with this complete kit. Includes soil moisture sensors, temperature sensors, ESP8266 microcontroller, and comprehensive educational guide.',
                'short_description': 'Build your own smart farm monitoring system',
                'price': 4500.00,
                'compare_price': 5500.00,
                'stock': 50,
                'category_slug': 'science-kits',
                'product_type': 'science_kit',
                'xp_reward': 100,
                'age_group': '10-16',
                'difficulty_level': 'intermediate',
                'is_featured': True,
                'includes': 'ESP8266, soil moisture sensor, DHT11 temperature sensor, breadboard, jumper wires, USB cable, guide book',
                'requirements': 'Computer with internet connection, basic understanding of electronics',
                'specifications': {'weight': '0.5kg', 'dimensions': '30x20x5cm', 'power': '5V USB'},
            },
            {
                'name': 'DIY Solar System Model Kit',
                'description': 'Build a working model of the solar system with this educational kit. Learn about planets, orbits, and space science.',
                'short_description': 'Create your own solar system model',
                'price': 2500.00,
                'stock': 40,
                'category_slug': 'science-kits',
                'product_type': 'science_kit',
                'xp_reward': 60,
                'age_group': '8-14',
                'difficulty_level': 'intermediate',
                'includes': 'Planet models, motor, paint, brush, educational booklet',
            },
            {
                'name': 'Green Energy Science Kit',
                'description': 'Explore renewable energy with solar, wind, and hydro power experiments. Build working models of each energy source.',
                'short_description': 'Learn about renewable energy',
                'price': 3200.00,
                'stock': 35,
                'category_slug': 'science-kits',
                'product_type': 'science_kit',
                'xp_reward': 80,
                'age_group': '10-16',
                'difficulty_level': 'intermediate',
                'is_best_seller': True,
            },
            
            # ============================================================
            # ELECTRONICS
            # ============================================================
            {
                'name': 'Arduino Starter Kit',
                'description': 'Complete Arduino kit with 15 projects. Perfect for beginners learning electronics and programming. Includes Arduino Uno, sensors, LEDs, motors, and project guide.',
                'short_description': 'The perfect start for electronics beginners',
                'price': 3500.00,
                'compare_price': 4500.00,
                'stock': 100,
                'category_slug': 'electronics',
                'product_type': 'electronics',
                'xp_reward': 75,
                'age_group': '12+',
                'difficulty_level': 'beginner',
                'is_featured': True,
                'includes': 'Arduino Uno, breadboard, 15+ sensors, LEDs, resistors, motors, project guide',
            },
            {
                'name': 'Sensor Pack: Temperature, Humidity, Light',
                'description': 'Essential sensors for science fair projects and IoT experiments. Includes DHT11 temperature/humidity, LDR light sensor, and thermistor modules.',
                'short_description': 'Essential sensor pack for projects',
                'price': 1200.00,
                'stock': 75,
                'category_slug': 'electronics',
                'product_type': 'electronics',
                'xp_reward': 50,
                'age_group': '10+',
                'difficulty_level': 'beginner',
                'includes': 'DHT11 sensor, LDR module, thermistor, connecting cables',
            },
            {
                'name': 'Raspberry Pi 4 Starter Kit',
                'description': 'Complete Raspberry Pi 4 kit with case, power supply, microSD card, and beginner projects. Perfect for learning programming and building IoT projects.',
                'short_description': 'Complete Raspberry Pi 4 starter kit',
                'price': 8500.00,
                'stock': 25,
                'category_slug': 'electronics',
                'product_type': 'electronics',
                'xp_reward': 150,
                'age_group': '14+',
                'difficulty_level': 'intermediate',
                'is_featured': True,
            },
            {
                'name': 'LED Matrix Display',
                'description': '8x8 LED matrix display with MAX7219 driver. Perfect for text scrolling, animations, and science fair projects.',
                'short_description': 'Programmable LED matrix display',
                'price': 850.00,
                'stock': 60,
                'category_slug': 'electronics',
                'product_type': 'electronics',
                'xp_reward': 30,
                'age_group': '10+',
                'difficulty_level': 'beginner',
            },
            
            # ============================================================
            # READATHON BOOKS
            # ============================================================
            {
                'name': 'Maya and the Smart Farm',
                'description': 'A story about a young innovator who uses technology to solve farm challenges in her community. Inspires critical thinking and innovation.',
                'short_description': 'An inspiring story about innovation',
                'price': 599.00,
                'stock': 200,
                'category_slug': 'readathon-books',
                'product_type': 'book',
                'xp_reward': 25,
                'age_group': '8-12',
                'difficulty_level': 'beginner',
                'is_featured': True,
                'pages': 120,
                'reading_level': 'Grade 4-6',
            },
            {
                'name': 'The Secret of the Solar Panel',
                'description': 'Join Mia and her friends as they uncover the mystery behind solar energy. A fun adventure that teaches about renewable energy.',
                'short_description': 'A mystery adventure about solar energy',
                'price': 699.00,
                'stock': 150,
                'category_slug': 'readathon-books',
                'product_type': 'book',
                'xp_reward': 30,
                'age_group': '9-13',
                'difficulty_level': 'intermediate',
                'is_best_seller': True,
                'pages': 150,
                'reading_level': 'Grade 4-7',
            },
            {
                'name': 'Efunza Coding Adventures',
                'description': 'Learn programming through exciting stories and hands-on activities. Perfect for young coders starting their journey.',
                'short_description': 'Learn coding through stories',
                'price': 799.00,
                'stock': 100,
                'category_slug': 'readathon-books',
                'product_type': 'book',
                'xp_reward': 40,
                'age_group': '10-14',
                'difficulty_level': 'intermediate',
                'pages': 180,
                'reading_level': 'Grade 5-8',
            },
            {
                'name': 'Robots in the Classroom',
                'description': 'How robots are changing education. Real stories from teachers and students who use robotics in learning.',
                'short_description': 'Real stories about robotics in education',
                'price': 899.00,
                'stock': 80,
                'category_slug': 'readathon-books',
                'product_type': 'book',
                'xp_reward': 45,
                'age_group': '12+',
                'difficulty_level': 'advanced',
                'pages': 220,
                'reading_level': 'Grade 7+',
            },
            
            # ============================================================
            # ROBOTICS KITS
            # ============================================================
            {
                'name': 'Robotics Competition Kit',
                'description': 'Build and program a competition-ready robot. Includes motors, sensors, chassis, and code examples. Perfect for robotics clubs and competitions.',
                'short_description': 'Build competition-ready robots',
                'price': 8500.00,
                'compare_price': 10500.00,
                'stock': 30,
                'category_slug': 'robotics',
                'product_type': 'science_kit',
                'xp_reward': 200,
                'age_group': '12-18',
                'difficulty_level': 'advanced',
                'is_featured': True,
                'includes': 'Robot chassis, motors, wheels, ultrasonic sensor, IR sensor, Arduino Mega, motor driver, battery pack',
                'requirements': 'Previous experience with Arduino or robotics recommended',
            },
            {
                'name': 'Mini Robot Car Kit',
                'description': 'Build your own robot car with obstacle avoidance and line-following capabilities. Fun and educational for beginners.',
                'short_description': 'Build a smart robot car',
                'price': 2800.00,
                'stock': 45,
                'category_slug': 'robotics',
                'product_type': 'science_kit',
                'xp_reward': 60,
                'age_group': '10-16',
                'difficulty_level': 'intermediate',
                'includes': 'Robot chassis, motors, wheels, ultrasonic sensor, IR sensors, Arduino Nano, battery case',
            },
            {
                'name': 'Robotic Arm Kit',
                'description': 'Build a fully functional robotic arm with 4 degrees of freedom. Learn about mechanics, servos, and programming.',
                'short_description': 'Build a robotic arm',
                'price': 6500.00,
                'stock': 20,
                'category_slug': 'robotics',
                'product_type': 'science_kit',
                'xp_reward': 150,
                'age_group': '14+',
                'difficulty_level': 'advanced',
                'is_best_seller': True,
            },
            
            # ============================================================
            # STEM KITS
            # ============================================================
            {
                'name': 'Complete STEM Learning Kit',
                'description': 'All-in-one STEM kit covering science, technology, engineering, and math through hands-on projects.',
                'short_description': 'Complete STEM learning in one box',
                'price': 12000.00,
                'stock': 15,
                'category_slug': 'stem-kits',
                'product_type': 'science_kit',
                'xp_reward': 250,
                'age_group': '8-16',
                'difficulty_level': 'intermediate',
                'is_featured': True,
                'includes': 'Arduino, sensors, motors, science experiment materials, project guide, workbooks',
            },
            
            # ============================================================
            # MERCHANDISE
            # ============================================================
            {
                'name': 'Efunza T-Shirt - Innovator',
                'description': 'Premium quality cotton t-shirt with the Efunza Innovator design. Perfect for makers and young innovators.',
                'short_description': 'Premium Efunza brand t-shirt',
                'price': 1200.00,
                'stock': 100,
                'category_slug': 'merchandise',
                'product_type': 'merchandise',
                'xp_reward': 10,
                'age_group': 'All',
                'difficulty_level': 'beginner',
                'specifications': {'material': '100% cotton', 'sizes': 'S, M, L, XL, XXL'},
            },
            {
                'name': 'Efunza Backpack - Maker Edition',
                'description': 'Durable backpack for carrying your projects and gear. Perfect for school, makerspaces, and competitions.',
                'short_description': 'Maker edition backpack',
                'price': 2500.00,
                'stock': 50,
                'category_slug': 'merchandise',
                'product_type': 'merchandise',
                'xp_reward': 20,
                'age_group': 'All',
                'difficulty_level': 'beginner',
            },
            {
                'name': 'Efunza Sticker Pack',
                'description': 'Set of 20 premium vinyl stickers featuring Efunza designs. Perfect for laptops, water bottles, and notebooks.',
                'short_description': 'Efunza sticker collection',
                'price': 299.00,
                'stock': 300,
                'category_slug': 'merchandise',
                'product_type': 'merchandise',
                'xp_reward': 5,
                'age_group': 'All',
                'difficulty_level': 'beginner',
                'is_best_seller': True,
            },
            
            # ============================================================
            # DIGITAL PRODUCTS
            # ============================================================
            {
                'name': 'E-Coding - Python Basics Course',
                'description': 'Interactive Python programming course for beginners. Learn through projects and challenges.',
                'short_description': 'Learn Python programming',
                'price': 500.00,
                'stock': 999,
                'category_slug': 'digital',
                'product_type': 'digital',
                'xp_reward': 50,
                'age_group': '12+',
                'difficulty_level': 'beginner',
                'is_digital': True,
                'is_featured': True,
            },
            {
                'name': 'Robotics Project PDF Bundle',
                'description': 'Collection of 20 robotics projects with detailed instructions, code, and schematics.',
                'short_description': '20 robotics projects guide',
                'price': 350.00,
                'stock': 999,
                'category_slug': 'digital',
                'product_type': 'digital',
                'xp_reward': 35,
                'age_group': '10+',
                'difficulty_level': 'intermediate',
                'is_digital': True,
            },
        ]
        
        created_count = 0
        for product_data in products:
            category_slug = product_data.pop('category_slug')
            category = categories.get(category_slug)
            
            if not category:
                self.stdout.write(self.style.WARNING(f"  ⚠️ Category '{category_slug}' not found, skipping product"))
                continue
            
            # Set product_type based on category if not specified
            if 'product_type' not in product_data:
                if category_slug in ['science-kits', 'robotics', 'stem-kits']:
                    product_data['product_type'] = 'science_kit'
                elif category_slug == 'electronics':
                    product_data['product_type'] = 'electronics'
                elif category_slug == 'readathon-books':
                    product_data['product_type'] = 'book'
                elif category_slug == 'merchandise':
                    product_data['product_type'] = 'merchandise'
                elif category_slug == 'digital':
                    product_data['product_type'] = 'digital'
                else:
                    product_data['product_type'] = 'science_kit'
            
            # Create or update product
            product, created = Product.objects.get_or_create(
                name=product_data['name'],
                defaults=product_data
            )
            
            if created:
                product.categories.add(category)
                created_count += 1
                self.stdout.write(f"  ✅ Created: {product.name}")
            else:
                # Update existing product
                for key, value in product_data.items():
                    setattr(product, key, value)
                product.save()
                product.categories.add(category)  # Ensure category is added
                self.stdout.write(f"  ↻ Updated: {product.name}")
        
        self.stdout.write(self.style.SUCCESS(f"📦 Created/Updated {created_count} new products"))
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print store summary statistics"""
        total_categories = ProductCategory.objects.count()
        total_products = Product.objects.count()
        featured_products = Product.objects.filter(is_featured=True).count()
        best_sellers = Product.objects.filter(is_best_seller=True).count()
        digital_products = Product.objects.filter(is_digital=True).count()
        
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("📊 STORE SUMMARY")
        self.stdout.write("=" * 60)
        self.stdout.write(f"  Categories: {total_categories}")
        self.stdout.write(f"  Products: {total_products}")
        self.stdout.write(f"  Featured Products: {featured_products}")
        self.stdout.write(f"  Best Sellers: {best_sellers}")
        self.stdout.write(f"  Digital Products: {digital_products}")
        self.stdout.write("=" * 60)