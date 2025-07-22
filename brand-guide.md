# Promtitude Brand Guidelines

## Logo Overview

The Promtitude logo represents the intersection of precision recruiting and AI technology through a minimalist "P" integrated with circuit patterns. The ultra-thin design conveys sophistication and technological advancement.

## Logo Files

### Primary Logos
- `logo-final.svg` - Primary logo (scalable, color-adaptive)
- `logo-brand-colors.svg` - Brand color version
- `logo-horizontal.svg` - Horizontal layout with wordmark

### Icon Versions
- `logo-icon.svg` - Square icon for apps
- `favicon.svg` - 32x32 optimized favicon

### Platform-Specific
- `logo-linkedin-final.svg` - LinkedIn optimized (400x400)

## Logo Usage

### Minimum Sizes
- Full logo: 40px height minimum
- Icon only: 16px minimum
- Horizontal logo: 120px width minimum

### Clear Space
Maintain clear space around the logo equal to the height of the circuit node (the small square elements).

### Positioning
- The circuit traces should always extend outward, never inward
- Maintain the precise angles - do not skew or distort

## Color Specifications

### Primary Colors
- **Promtitude Purple**: #4F46E5 (Primary brand color)
- **Light Purple**: #818CF8 (Accent, circuit traces)
- **Black**: #1A1A1A (Text and monochrome logo)
- **White**: #FFFFFF (Reverse applications)

### Usage Rules
1. **On light backgrounds**: Use black (#1A1A1A) or brand purple (#4F46E5)
2. **On dark backgrounds**: Use white (#FFFFFF)
3. **On purple backgrounds**: Use white only
4. **Circuit traces**: Can be shown in light purple (#818CF8) for emphasis

## Typography

### Logo Wordmark
- Font: Arial or system sans-serif
- Weight: 300 (Light)
- Tracking: Normal
- Case: UPPERCASE

### Supporting Text
- Headers: Sans-serif, medium weight
- Body: Sans-serif, regular weight

## Incorrect Usage

### Don't:
- ❌ Rotate the logo
- ❌ Change the stroke width
- ❌ Add effects (shadows, gradients, outlines)
- ❌ Change the proportions
- ❌ Use colors outside the brand palette
- ❌ Remove the circuit elements
- ❌ Round the corners

### Do:
- ✅ Maintain the square line caps
- ✅ Keep all elements proportional
- ✅ Use approved colors only
- ✅ Ensure sufficient contrast

## Applications

### Digital
- Website headers: Use `logo-horizontal.svg`
- App icons: Use `logo-icon.svg`
- Social media profiles: Use `logo-linkedin-final.svg`
- Email signatures: Use `logo-final.svg` at 40px height

### Print
- Business cards: Minimum 0.5 inch height
- Letterhead: 0.75 inch height
- Large format: No maximum size

## File Formats

### For Digital
- SVG (preferred) - Scalable and color-adaptive
- PNG - For platforms that don't support SVG
  - Export at 2x resolution for retina displays

### For Print
- SVG or PDF - Vector formats preferred
- EPS - For legacy systems
- Never use raster formats for print

## Implementation Code

### CSS Variables
```css
:root {
  --promtitude-purple: #4F46E5;
  --promtitude-purple-light: #818CF8;
  --promtitude-black: #1A1A1A;
}
```

### React Component Usage
```jsx
import { ReactComponent as Logo } from '@/public/logo-final.svg';

<Logo className="h-10 w-auto text-purple-600" />
```

## Brand Voice

The Promtitude logo should always be presented in contexts that reinforce:
- **Precision**: Clean, organized layouts
- **Innovation**: Modern, forward-thinking design
- **Professionalism**: Business-appropriate applications
- **Intelligence**: Thoughtful, strategic placement

## Contact

For brand-related questions or custom logo applications, contact: promtitude@gmail.com

---

*Last updated: July 2025*