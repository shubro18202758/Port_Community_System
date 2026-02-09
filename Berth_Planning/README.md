# Berth Planning System - HTML Prototypes

## 📦 What's Inside

This folder contains **4 standalone HTML prototypes** that you can open directly in any web browser!

### Files:

1. **index.html** - Landing page with links to all prototypes
2. **dashboard.html** - Main operational dashboard
3. **berth-management.html** - Berth configuration and management
4. **3d-port-view.html** - 3D port visualization

---

## 🚀 How to Use

### Option 1: Start with Index Page
1. Open `index.html` in your web browser
2. Click on any page card to navigate to that prototype

### Option 2: Open Individual Pages
1. Double-click any `.html` file
2. It will open in your default web browser
3. Everything works without any installation!

---

## ✨ What Makes These Special

### ✅ Standalone HTML Files
- No Angular required
- No npm install needed
- No build process
- **Just open and view!**

### ✅ Beautiful Design
- Modern gradient backgrounds
- Smooth animations
- Responsive layout
- Professional UI

### ✅ Interactive Features
- Live clock updates
- Clickable elements
- Hover effects
- Color-coded status

---

## 📄 Page Details

### 1. Dashboard (dashboard.html)
**Main Operational Dashboard**

**Features:**
- 4 KPI Cards with gradients
  - Vessels in Port
  - Berth Utilization (with progress bar)
  - Vessels in Queue
  - Active Alerts (with pulse animation)

- Interactive Timeline
  - Gantt-style berth schedule
  - Visual allocation blocks
  - Animated glow effect
  - Click to view vessel details

- Vessel Queue (Right Sidebar)
  - Priority-based listing
  - Waiting time tracking
  - ETA display

- Active Alerts
  - Color-coded warnings
  - Weather alerts
  - Delay notifications

- AI Recommendations
  - Confidence scores
  - Time savings
  - One-click apply

**Technologies:**
- HTML5
- CSS3 (Gradients, Animations)
- JavaScript (Real-time clock)
- Font Awesome Icons

---

### 2. Berth Management (berth-management.html)
**Berth Configuration & Management**

**Features:**
- Page Header
  - Add New Berth button
  - Import Template option

- Statistics Bar
  - Active: 12
  - Maintenance: 2
  - Inactive: 1
  - Total: 15

- Advanced Filters
  - Search by code/name
  - Filter by type
  - Filter by status
  - View mode toggle (Table/Grid)

- Berth Table
  - Code, Name, Type
  - Specifications (length, draft)
  - Status (color-coded tags)
  - Equipment list
  - Current vessel
  - Action buttons (View, Edit, Status, Delete)

**Technologies:**
- HTML5 Tables
- CSS3 Styling
- Font Awesome Icons
- Responsive Grid

---

### 3. 3D Port View (3d-port-view.html)
**Interactive 3D Port Visualization**

**Features:**
- Control Bar
  - Port selector dropdown
  - Settings button
  - Screenshot button
  - Reset view button

- 3D Viewport
  - Gradient sky background
  - 4 berths displayed
  - Color-coded status:
    - 🟢 Green = Available
    - 🔴 Red = Occupied
  - Vessel icons on occupied berths
  - Hover effects (lift up)

- Help Text Overlay
  - Click: Select berth/vessel
  - Drag: Rotate view
  - Scroll: Zoom in/out

- Information Panel (Right Side)
  - Port statistics
  - Berth details on click
  - Current vessel info

- Legend (Bottom Left)
  - Color explanations
  - Status indicators

**Technologies:**
- HTML5
- CSS3 (3D-style effects)
- JavaScript (Click handling)
- Gradient backgrounds
- Font Awesome Icons

---

## 🎨 Design Features

### Color Palette
```
Primary Blue:   #3498db
Success Green:  #27ae60
Warning Orange: #f39c12
Danger Red:     #e74c3c
Background:     #f5f7fa
Text Dark:      #2c3e50
Text Light:     #7f8c8d
```

### Gradients Used
```css
Purple Gradient:  linear-gradient(135deg, #667eea, #764ba2)
Pink Gradient:    linear-gradient(135deg, #f093fb, #f5576c)
Blue Gradient:    linear-gradient(135deg, #4facfe, #00f2fe)
Green Gradient:   linear-gradient(135deg, #43e97b, #38f9d7)
```

### Animations
- Pulse glow on active alerts
- Hover lift effects
- Smooth transitions
- Real-time clock updates

---

## 💡 Key Differences from Angular Components

### Angular Components (Previous Files)
- Required Angular framework
- Used `{{ }}` syntax for data binding
- Needed `npm install` and build process
- Required TypeScript compilation

### HTML Prototypes (These Files)
- ✅ Pure HTML/CSS/JavaScript
- ✅ No framework needed
- ✅ Open directly in browser
- ✅ Static sample data
- ✅ Work offline

---

## 🌐 Browser Compatibility

Works in all modern browsers:
- ✅ Chrome/Edge (latest)
- ✅ Firefox (latest)
- ✅ Safari (latest)
- ✅ Mobile browsers

**Requirements:**
- JavaScript enabled
- Internet connection (for Font Awesome icons)

---

## 📱 Responsive Design

All pages adapt to different screen sizes:
- **Desktop (>1200px):** Full layout with sidebars
- **Tablet (768-1199px):** Stacked columns
- **Mobile (<768px):** Single column

Test by resizing your browser window!

---

## 🎯 Next Steps

### To Convert to Angular:
1. Use these as design reference
2. Copy HTML structure to Angular templates
3. Replace static data with API calls
4. Add Angular directives (*ngFor, *ngIf, etc.)
5. Connect to backend services

### To Customize:
1. Open any `.html` file in a text editor
2. Find the `<style>` section
3. Change colors, sizes, fonts as needed
4. Find the `<script>` section to change data
5. Save and refresh browser

---

## 📊 Sample Data Included

Each page has realistic sample data:
- 12 vessels in port
- 85% berth utilization
- 3 vessels in queue
- 2 active alerts
- 15 total berths
- AI recommendations with 94% confidence

---

## 🔧 Customization Guide

### Change Colors:
Look for these CSS variables:
```css
background: linear-gradient(...);
color: #3498db;
```

### Change Data:
Look for JavaScript objects:
```javascript
const berthData = {
    'A-1': { ... },
    'A-2': { ... }
};
```

### Add More Berths:
Copy existing HTML structure and modify:
```html
<div class="berth berth-available">
    <div class="berth-label">NEW-1</div>
</div>
```

---

## 🎉 Ready to Present!

These prototypes are perfect for:
- ✅ Stakeholder demonstrations
- ✅ User feedback sessions
- ✅ Design reviews
- ✅ Development reference
- ✅ Client presentations

**Just open `index.html` and start exploring!**

---

## 📞 Support

If you need:
- More pages
- Different layouts
- Additional features
- Custom data
- Integration help

Just ask! I can create more prototypes or modify existing ones.

---

**Created:** January 2026  
**For:** Kale Logistics Solutions Private Limited  
**Project:** Berth Planning & Allocation Optimization  
**Type:** Standalone HTML Prototypes
