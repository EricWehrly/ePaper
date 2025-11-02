# ePaper UI Redesign Roadmap

## 🎯 **Project Overview**
Transform the current ePaper interface into a modern, tab-based system that works seamlessly on both desktop and mobile devices.

## 📱 **Target Architecture**

### **Main Components**
1. **Display** - Current/Preview views of e-paper (collapsible, always present)
2. **Library** - Thumbnail gallery with details and view modifiers
3. **Playlists** - Playlist management and playback
4. **Photos** - Google Photos integration
5. **Controls** - Display settings & playback controls
6. **Settings** - User/system configuration (future)

### **Layout Strategy**
- **Desktop**: Horizontal tabs with side-by-side display and content
- **Mobile**: Vertical scroll with flyout side menu, collapsible display area
- **Responsive**: Mobile-first approach with desktop enhancements

---

## 🚀 **Implementation Phases**

### **Phase 1: CSS Architecture Foundation** ✅
- [x] Split `style.css` into modular files
- [x] Create `css/common.css` - Base styles, variables, components
- [x] Create `css/desktop.css` - Desktop-specific layouts and interactions
- [x] Create `css/mobile.css` - Mobile layouts and touch interactions
- [x] Create `css/components.css` - Reusable UI components
- [x] Set up responsive breakpoint system
- [x] Implement CSS custom properties for theming
- [x] Add display area show/hide functionality

### **Phase 2: Core Tab System**
- [ ] Create main tab navigation component
- [ ] Implement tab switching with URL history support
- [ ] Add smooth transitions between tabs
- [ ] Create mobile flyout menu structure
- [ ] Add hamburger menu for mobile navigation
- [ ] Implement swipe gestures for mobile tab switching

### **Phase 3: Enhanced Display Area**
- [ ] Make display area collapsible/expandable
- [ ] Improve Current/Preview tab switching
- [ ] Add display area controls (minimize/maximize)
- [ ] Optimize display area for mobile viewing
- [ ] Add touch-friendly interactions for mobile

### **Phase 4: Library Tab Enhancement**
- [ ] Create image details panel component
- [ ] Add file metadata display (name, size, format, dimensions)
- [ ] Show e-paper conversion status and actions
- [ ] Create view modifiers UI framework
- [ ] Add search bar placeholder
- [ ] Add sort dropdown (name, date, size, format)
- [ ] Add filter toggles (converted, favorites, etc.)
- [ ] Implement grid/list view toggle
- [ ] Add thumbnail selection and multi-select capabilities

### **Phase 5: Playlist Tab Polish**
- [ ] Enhance playlist management UI
- [ ] Add drag-and-drop playlist creation
- [ ] Improve playlist preview functionality
- [ ] Add playlist metadata and controls
- [ ] Create playlist sharing/export options

### **Phase 6: Photos Tab Integration**
- [ ] Streamline Google Photos picker interface
- [ ] Add batch selection and download progress
- [ ] Integrate photo import with library view
- [ ] Add photo metadata preservation

### **Phase 7: Controls Tab Consolidation**
- [ ] Move display controls to dedicated tab
- [ ] Create unified control interface
- [ ] Add advanced display settings
- [ ] Implement control presets/profiles

### **Phase 8: Mobile Experience Polish**
- [ ] Optimize touch interactions throughout
- [ ] Add pull-to-refresh functionality
- [ ] Implement haptic feedback where appropriate
- [ ] Add mobile-specific gestures (swipe, pinch, etc.)
- [ ] Optimize performance for mobile devices

### **Phase 9: Settings Tab (Future)**
- [ ] Create user preferences interface
- [ ] Add system configuration options
- [ ] Implement theme switching
- [ ] Add backup/restore functionality
- [ ] Create user account management

---

## 🎨 **CSS Architecture Details**

### **File Structure**
```
src/web/static/css/
├── common.css      # Base styles, variables, mobile-first defaults
├── desktop.css     # Desktop enhancements (@media queries)
├── mobile.css      # Mobile-specific styles and interactions
└── components.css  # Reusable UI components and utilities
```

### **Responsive Breakpoints**
```css
/* Mobile first (default) */
/* Tablet: 768px and up */
/* Desktop: 1024px and up */
/* Large desktop: 1440px and up */
```

### **CSS Custom Properties Theme**
```css
:root {
  --primary-color: #007acc;
  --secondary-color: #f0f0f0;
  --accent-color: #ff6b35;
  --text-color: #333;
  --background-color: #fff;
  --border-color: #ddd;
  --border-radius: 8px;
  --spacing-sm: 0.5rem;
  --spacing-md: 1rem;
  --spacing-lg: 2rem;
  --transition-fast: 0.2s ease;
  --transition-slow: 0.4s ease;
}
```

---

## 🔍 **Key Features**

### **Display Area Enhancements**
- ✅ Collapsible display area for mobile space optimization
- ✅ Always present but hideable for focused content viewing
- ✅ Smooth show/hide animations
- ✅ Touch-friendly controls

### **View Modifiers (Future-Ready)**
- 🔍 **Search**: Real-time filtering by filename, metadata
- 📊 **Sort**: Name, date, size, format, conversion status
- 🏷️ **Filter**: File type, conversion status, playlist membership
- 📱 **View**: Grid/list toggle, thumbnail size adjustment

### **Mobile-First Benefits**
- 📱 Touch-optimized interfaces
- 🎯 Focused single-task views
- ⚡ Fast navigation with flyout menu
- 💾 Minimal UI for small screens

### **Desktop Enhancements**
- 🖱️ Hover states and keyboard shortcuts
- 📐 Multi-column layouts
- 🔄 Drag-and-drop functionality
- 📊 Rich information density

---

## ✅ **Success Criteria**

### **Phase 1 Complete When:**
- [ ] Modular CSS files are created and working
- [ ] Responsive design foundation is established
- [ ] Display area show/hide functionality works
- [ ] No visual regressions in current functionality

### **Phase 2 Complete When:**
- [ ] Tab navigation works on desktop and mobile
- [ ] Mobile flyout menu is functional
- [ ] URL history integration works
- [ ] Smooth transitions are implemented

### **Phase 3 Complete When:**
- [ ] Display area is fully collapsible
- [ ] Mobile display optimization is complete
- [ ] Touch interactions are responsive

### **Final Success Criteria:**
- [ ] Mobile experience is smooth and intuitive
- [ ] Desktop experience is feature-rich and efficient
- [ ] All current functionality is preserved
- [ ] New features enhance usability
- [ ] Performance is maintained or improved
- [ ] Code is maintainable and well-documented

---

## 📝 **Development Notes**

### **Current Status:** Phase 1 Complete ✅ - Ready for Phase 2
**Next Steps:** 
1. Create main tab navigation component
2. Implement tab switching with URL history support
3. Add mobile flyout menu structure

### **Technical Decisions:**
- **CSS**: Mobile-first responsive design with progressive enhancement
- **JavaScript**: Maintain existing modular structure
- **Performance**: Minimize CSS file size, optimize for mobile loading
- **Accessibility**: Maintain ARIA labels and keyboard navigation
- **Browser Support**: Modern browsers (ES6+, CSS Grid, Flexbox)

---

*Last Updated: November 2, 2025*
*Current Phase: 1 - CSS Architecture Foundation*