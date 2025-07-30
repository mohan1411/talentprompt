# Smart Talent Radar Technical Implementation

## Table of Contents
1. [How Smart Talent Radar Works](#how-smart-talent-radar-works)
2. [Canvas-Based Visualization](#canvas-based-visualization)
3. [Force-Directed Layout Algorithm](#force-directed-layout-algorithm)
4. [Interactive Features](#interactive-features)
5. [Data Mapping & Scaling](#data-mapping--scaling)
6. [Performance Optimization](#performance-optimization)
7. [Real-World Examples](#real-world-examples)
8. [Future Enhancements](#future-enhancements)

## How Smart Talent Radar Works

Smart Talent Radar provides an intuitive visual representation of your candidate landscape, showing relationships, availability, and match quality at a glance.

### User Experience

```
Search Results → Radar Visualization
                        │
    ┌───────────────────┼───────────────────┐
    │                   │                   │
    │    ● ← High Match│    ○ ← Good Match│
    │   ● ●             │         ○         │
    │  ●   ●            │       ○   ○       │
    │ ●     ● (You)     │     ○       ○     │
    │  ●   ●            │       ○   ○       │
    │   ● ●             │         ○         │
    │    ●              │    ○              │
    └───────────────────┴───────────────────┘
         Inner Circle         Outer Circle
         (Best Matches)     (Good Matches)

Legend:
● Size = Experience Level
● Color = Availability (Green/Orange/Red)
● Distance = Match Relevance
● Clustering = Similar Candidates
```

### Visual Elements

```typescript
interface RadarCandidate {
  id: string;
  name: string;
  title: string;
  
  // Position
  x: number;          // X coordinate on canvas
  y: number;          // Y coordinate on canvas
  angle: number;      // Angle from center (radians)
  distance: number;   // Distance from center (0-1)
  
  // Visual properties
  radius: number;     // Dot size (based on experience)
  color: string;      // Availability color
  opacity: number;    // Match confidence
  
  // Data
  score: number;      // Match score (0-1)
  availability: number;
  experience: number;
  skills: string[];
  
  // Interaction
  hovered: boolean;
  selected: boolean;
  cluster?: string;   // Cluster ID for grouping
}
```

## Canvas-Based Visualization

### Core Canvas Renderer

```typescript
export class TalentRadarRenderer {
  private canvas: HTMLCanvasElement;
  private ctx: CanvasRenderingContext2D;
  private animationFrame: number;
  
  constructor(canvas: HTMLCanvasElement) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d')!;
    this.setupCanvas();
  }
  
  private setupCanvas() {
    // Handle high DPI displays
    const dpr = window.devicePixelRatio || 1;
    const rect = this.canvas.getBoundingClientRect();
    
    this.canvas.width = rect.width * dpr;
    this.canvas.height = rect.height * dpr;
    
    this.ctx.scale(dpr, dpr);
    
    // Set canvas properties
    this.canvas.style.width = rect.width + 'px';
    this.canvas.style.height = rect.height + 'px';
  }
  
  render(candidates: RadarCandidate[], options: RenderOptions) {
    // Clear canvas
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    
    const centerX = this.canvas.width / 2;
    const centerY = this.canvas.height / 2;
    const maxRadius = Math.min(centerX, centerY) * 0.9;
    
    // Draw background circles
    this.drawBackgroundCircles(centerX, centerY, maxRadius);
    
    // Draw candidates
    candidates.forEach(candidate => {
      this.drawCandidate(candidate, centerX, centerY, maxRadius);
    });
    
    // Draw connections for clusters
    this.drawClusterConnections(candidates, centerX, centerY);
    
    // Draw labels for hovered candidates
    const hoveredCandidate = candidates.find(c => c.hovered);
    if (hoveredCandidate) {
      this.drawTooltip(hoveredCandidate, centerX, centerY);
    }
  }
}
```

### Drawing Individual Candidates

```typescript
private drawCandidate(
  candidate: RadarCandidate,
  centerX: number,
  centerY: number,
  maxRadius: number
) {
  // Calculate position
  const x = centerX + Math.cos(candidate.angle) * candidate.distance * maxRadius;
  const y = centerY + Math.sin(candidate.angle) * candidate.distance * maxRadius;
  
  // Update candidate position for interaction
  candidate.x = x;
  candidate.y = y;
  
  // Draw outer glow for selected/hovered
  if (candidate.selected || candidate.hovered) {
    this.ctx.beginPath();
    const gradient = this.ctx.createRadialGradient(x, y, 0, x, y, candidate.radius * 2);
    gradient.addColorStop(0, `${candidate.color}88`);
    gradient.addColorStop(1, 'transparent');
    this.ctx.fillStyle = gradient;
    this.ctx.arc(x, y, candidate.radius * 2, 0, Math.PI * 2);
    this.ctx.fill();
  }
  
  // Draw main circle
  this.ctx.beginPath();
  this.ctx.fillStyle = candidate.color;
  this.ctx.globalAlpha = candidate.opacity;
  this.ctx.arc(x, y, candidate.radius, 0, Math.PI * 2);
  this.ctx.fill();
  
  // Draw border
  this.ctx.strokeStyle = 'white';
  this.ctx.lineWidth = 2;
  this.ctx.stroke();
  
  this.ctx.globalAlpha = 1;
  
  // Draw experience indicator (inner circle)
  if (candidate.experience > 10) {
    this.ctx.beginPath();
    this.ctx.fillStyle = 'white';
    this.ctx.arc(x, y, 3, 0, Math.PI * 2);
    this.ctx.fill();
  }
}
```

### Background Grid

```typescript
private drawBackgroundCircles(centerX: number, centerY: number, maxRadius: number) {
  // Draw concentric circles
  const circles = [0.25, 0.5, 0.75, 1.0];
  
  circles.forEach((ratio, index) => {
    this.ctx.beginPath();
    this.ctx.strokeStyle = '#e5e7eb';
    this.ctx.lineWidth = 1;
    this.ctx.setLineDash([5, 5]);
    this.ctx.arc(centerX, centerY, maxRadius * ratio, 0, Math.PI * 2);
    this.ctx.stroke();
    
    // Add labels
    this.ctx.fillStyle = '#6b7280';
    this.ctx.font = '12px sans-serif';
    this.ctx.fillText(
      `${(1 - ratio) * 100}% match`,
      centerX + 5,
      centerY - maxRadius * ratio + 15
    );
  });
  
  this.ctx.setLineDash([]);
  
  // Draw center point
  this.ctx.beginPath();
  this.ctx.fillStyle = '#3b82f6';
  this.ctx.arc(centerX, centerY, 5, 0, Math.PI * 2);
  this.ctx.fill();
  
  // Center label
  this.ctx.fillStyle = '#1f2937';
  this.ctx.font = 'bold 14px sans-serif';
  this.ctx.textAlign = 'center';
  this.ctx.fillText('Your Search', centerX, centerY + 20);
  this.ctx.textAlign = 'left';
}
```

## Force-Directed Layout Algorithm

### Position Calculation

```typescript
class ForceDirectedLayout {
  private forces: Force[] = [];
  private damping = 0.9;
  private iterations = 50;
  
  constructor() {
    // Add default forces
    this.forces.push(new RepulsionForce(100));    // Keep candidates apart
    this.forces.push(new AttractionForce(0.1));   // Pull toward center
    this.forces.push(new ClusterForce(50));       // Group similar candidates
  }
  
  calculatePositions(candidates: RadarCandidate[]): void {
    // Initialize random positions
    candidates.forEach(candidate => {
      if (!candidate.angle) {
        candidate.angle = Math.random() * Math.PI * 2;
        candidate.distance = 0.2 + Math.random() * 0.8;
      }
      
      // Convert to cartesian
      candidate.x = Math.cos(candidate.angle) * candidate.distance;
      candidate.y = Math.sin(candidate.angle) * candidate.distance;
      
      // Initialize velocity
      candidate.vx = 0;
      candidate.vy = 0;
    });
    
    // Run simulation
    for (let i = 0; i < this.iterations; i++) {
      this.tick(candidates);
    }
    
    // Convert back to polar coordinates
    candidates.forEach(candidate => {
      candidate.angle = Math.atan2(candidate.y, candidate.x);
      candidate.distance = Math.sqrt(candidate.x ** 2 + candidate.y ** 2);
      
      // Clamp distance
      candidate.distance = Math.min(1, Math.max(0.1, candidate.distance));
    });
  }
  
  private tick(candidates: RadarCandidate[]) {
    // Reset forces
    candidates.forEach(c => {
      c.fx = 0;
      c.fy = 0;
    });
    
    // Apply all forces
    this.forces.forEach(force => {
      force.apply(candidates);
    });
    
    // Update positions
    candidates.forEach(candidate => {
      // Apply forces to velocity
      candidate.vx = (candidate.vx + candidate.fx) * this.damping;
      candidate.vy = (candidate.vy + candidate.fy) * this.damping;
      
      // Update position
      candidate.x += candidate.vx;
      candidate.y += candidate.vy;
    });
  }
}
```

### Force Implementations

```typescript
// Repulsion force - keeps candidates from overlapping
class RepulsionForce implements Force {
  constructor(private strength: number) {}
  
  apply(candidates: RadarCandidate[]) {
    for (let i = 0; i < candidates.length; i++) {
      for (let j = i + 1; j < candidates.length; j++) {
        const a = candidates[i];
        const b = candidates[j];
        
        const dx = b.x - a.x;
        const dy = b.y - a.y;
        const distance = Math.sqrt(dx * dx + dy * dy);
        
        if (distance < 0.1) continue; // Avoid division by zero
        
        // Calculate repulsion
        const force = this.strength / (distance * distance);
        const fx = (dx / distance) * force;
        const fy = (dy / distance) * force;
        
        // Apply forces
        a.fx -= fx;
        a.fy -= fy;
        b.fx += fx;
        b.fy += fy;
      }
    }
  }
}

// Cluster force - groups similar candidates
class ClusterForce implements Force {
  constructor(private strength: number) {}
  
  apply(candidates: RadarCandidate[]) {
    // Group by cluster
    const clusters = new Map<string, RadarCandidate[]>();
    
    candidates.forEach(candidate => {
      if (candidate.cluster) {
        if (!clusters.has(candidate.cluster)) {
          clusters.set(candidate.cluster, []);
        }
        clusters.get(candidate.cluster)!.push(candidate);
      }
    });
    
    // Apply attraction within clusters
    clusters.forEach(cluster => {
      if (cluster.length < 2) return;
      
      // Calculate cluster center
      const cx = cluster.reduce((sum, c) => sum + c.x, 0) / cluster.length;
      const cy = cluster.reduce((sum, c) => sum + c.y, 0) / cluster.length;
      
      // Pull toward center
      cluster.forEach(candidate => {
        const dx = cx - candidate.x;
        const dy = cy - candidate.y;
        
        candidate.fx += dx * this.strength * 0.01;
        candidate.fy += dy * this.strength * 0.01;
      });
    });
  }
}
```

## Interactive Features

### Mouse Interaction

```typescript
class RadarInteraction {
  private hoveredCandidate: RadarCandidate | null = null;
  private selectedCandidate: RadarCandidate | null = null;
  private isDragging = false;
  private zoom = 1;
  private rotation = 0;
  
  constructor(
    private canvas: HTMLCanvasElement,
    private getCandidates: () => RadarCandidate[],
    private onUpdate: () => void
  ) {
    this.setupEventListeners();
  }
  
  private setupEventListeners() {
    // Mouse move for hover
    this.canvas.addEventListener('mousemove', (e) => {
      const point = this.getMousePosition(e);
      const candidate = this.findCandidateAt(point.x, point.y);
      
      if (candidate !== this.hoveredCandidate) {
        if (this.hoveredCandidate) {
          this.hoveredCandidate.hovered = false;
        }
        if (candidate) {
          candidate.hovered = true;
          this.canvas.style.cursor = 'pointer';
        } else {
          this.canvas.style.cursor = 'default';
        }
        this.hoveredCandidate = candidate;
        this.onUpdate();
      }
    });
    
    // Click for selection
    this.canvas.addEventListener('click', (e) => {
      const point = this.getMousePosition(e);
      const candidate = this.findCandidateAt(point.x, point.y);
      
      if (this.selectedCandidate) {
        this.selectedCandidate.selected = false;
      }
      
      if (candidate) {
        candidate.selected = true;
        this.selectedCandidate = candidate;
        this.onCandidateSelect(candidate);
      } else {
        this.selectedCandidate = null;
      }
      
      this.onUpdate();
    });
    
    // Wheel for zoom
    this.canvas.addEventListener('wheel', (e) => {
      e.preventDefault();
      
      const delta = e.deltaY > 0 ? 0.9 : 1.1;
      this.zoom = Math.max(0.5, Math.min(3, this.zoom * delta));
      
      this.onUpdate();
    });
  }
  
  private findCandidateAt(x: number, y: number): RadarCandidate | null {
    const candidates = this.getCandidates();
    
    // Check in reverse order (top to bottom)
    for (let i = candidates.length - 1; i >= 0; i--) {
      const candidate = candidates[i];
      const dx = x - candidate.x;
      const dy = y - candidate.y;
      const distance = Math.sqrt(dx * dx + dy * dy);
      
      if (distance <= candidate.radius + 5) { // 5px tolerance
        return candidate;
      }
    }
    
    return null;
  }
}
```

### Touch Gestures

```typescript
class TouchGestureHandler {
  private touches: Map<number, Touch> = new Map();
  private lastPinchDistance = 0;
  
  handleTouchStart(e: TouchEvent) {
    e.preventDefault();
    
    Array.from(e.touches).forEach(touch => {
      this.touches.set(touch.identifier, {
        x: touch.clientX,
        y: touch.clientY,
        startX: touch.clientX,
        startY: touch.clientY
      });
    });
    
    if (e.touches.length === 2) {
      // Initialize pinch
      this.lastPinchDistance = this.getPinchDistance();
    }
  }
  
  handleTouchMove(e: TouchEvent) {
    e.preventDefault();
    
    if (e.touches.length === 1) {
      // Pan
      const touch = e.touches[0];
      const lastTouch = this.touches.get(touch.identifier);
      
      if (lastTouch) {
        const dx = touch.clientX - lastTouch.x;
        const dy = touch.clientY - lastTouch.y;
        
        this.onPan(dx, dy);
        
        lastTouch.x = touch.clientX;
        lastTouch.y = touch.clientY;
      }
    } else if (e.touches.length === 2) {
      // Pinch zoom
      const distance = this.getPinchDistance();
      const scale = distance / this.lastPinchDistance;
      
      this.onZoom(scale);
      
      this.lastPinchDistance = distance;
    }
  }
  
  private getPinchDistance(): number {
    const touches = Array.from(this.touches.values());
    if (touches.length < 2) return 0;
    
    const dx = touches[1].x - touches[0].x;
    const dy = touches[1].y - touches[0].y;
    
    return Math.sqrt(dx * dx + dy * dy);
  }
}
```

## Data Mapping & Scaling

### Candidate Positioning

```typescript
function mapCandidateToRadar(candidate: SearchResult): RadarCandidate {
  // Map score to distance (inverse - higher score = closer to center)
  const distance = 1 - (candidate.score || 0.5);
  
  // Distribute angles to avoid overlap
  const angleJitter = (Math.random() - 0.5) * 0.2;
  const baseAngle = hashStringToAngle(candidate.id);
  const angle = baseAngle + angleJitter;
  
  // Map experience to size
  const minRadius = 8;
  const maxRadius = 20;
  const experienceRatio = Math.min(candidate.years_experience / 20, 1);
  const radius = minRadius + (maxRadius - minRadius) * experienceRatio;
  
  // Map availability to color
  const color = getAvailabilityColor(candidate.availability_score);
  
  // Map confidence to opacity
  const opacity = 0.5 + (candidate.confidence || 0.5) * 0.5;
  
  return {
    id: candidate.id,
    name: candidate.name,
    title: candidate.current_title,
    x: 0, // Will be calculated
    y: 0, // Will be calculated
    angle,
    distance,
    radius,
    color,
    opacity,
    score: candidate.score,
    availability: candidate.availability_score,
    experience: candidate.years_experience,
    skills: candidate.skills,
    hovered: false,
    selected: false,
    cluster: identifyCluster(candidate)
  };
}

function getAvailabilityColor(availability: number): string {
  if (availability > 0.7) return '#10b981'; // Green
  if (availability > 0.4) return '#f59e0b'; // Orange
  return '#ef4444'; // Red
}

function hashStringToAngle(str: string): number {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) - hash) + str.charCodeAt(i);
    hash = hash & hash;
  }
  return (Math.abs(hash) % 360) * (Math.PI / 180);
}
```

### Clustering Algorithm

```typescript
function identifyCluster(candidate: SearchResult): string {
  // Simple clustering based on primary skill
  const primarySkill = candidate.skills[0]?.toLowerCase() || 'general';
  
  const clusterMap: Record<string, string> = {
    'python': 'backend',
    'java': 'backend',
    'javascript': 'frontend',
    'react': 'frontend',
    'aws': 'cloud',
    'docker': 'devops',
    'kubernetes': 'devops',
    'machine learning': 'ai',
    'data science': 'ai'
  };
  
  return clusterMap[primarySkill] || 'general';
}

// Advanced clustering using k-means
class KMeansClustering {
  cluster(candidates: RadarCandidate[], k: number = 5): Map<string, RadarCandidate[]> {
    // Convert candidates to feature vectors
    const vectors = candidates.map(c => this.candidateToVector(c));
    
    // Initialize centroids
    const centroids = this.initializeCentroids(vectors, k);
    
    // Iterate until convergence
    let iterations = 0;
    let hasChanged = true;
    
    while (hasChanged && iterations < 50) {
      hasChanged = false;
      
      // Assign to clusters
      const clusters = new Map<number, number[]>();
      
      vectors.forEach((vector, i) => {
        const nearestCentroid = this.findNearestCentroid(vector, centroids);
        
        if (!clusters.has(nearestCentroid)) {
          clusters.set(nearestCentroid, []);
        }
        clusters.get(nearestCentroid)!.push(i);
        
        // Update candidate cluster
        const oldCluster = candidates[i].cluster;
        candidates[i].cluster = `cluster-${nearestCentroid}`;
        
        if (oldCluster !== candidates[i].cluster) {
          hasChanged = true;
        }
      });
      
      // Update centroids
      this.updateCentroids(centroids, clusters, vectors);
      
      iterations++;
    }
    
    // Group candidates by cluster
    const result = new Map<string, RadarCandidate[]>();
    candidates.forEach(candidate => {
      if (!result.has(candidate.cluster!)) {
        result.set(candidate.cluster!, []);
      }
      result.get(candidate.cluster!)!.push(candidate);
    });
    
    return result;
  }
  
  private candidateToVector(candidate: RadarCandidate): number[] {
    // Create feature vector from candidate properties
    const vector: number[] = [];
    
    // Position features
    vector.push(candidate.score);
    vector.push(candidate.availability);
    vector.push(candidate.experience / 20); // Normalize
    
    // Skill features (one-hot encoding for top skills)
    const topSkills = ['python', 'javascript', 'java', 'react', 'aws'];
    topSkills.forEach(skill => {
      vector.push(candidate.skills.includes(skill) ? 1 : 0);
    });
    
    return vector;
  }
}
```

## Performance Optimization

### Canvas Optimization

```typescript
class OptimizedRadarRenderer {
  private offscreenCanvas: HTMLCanvasElement;
  private offscreenCtx: CanvasRenderingContext2D;
  private needsRedraw = true;
  private frameRequest: number;
  
  constructor(canvas: HTMLCanvasElement) {
    // Create offscreen canvas for double buffering
    this.offscreenCanvas = document.createElement('canvas');
    this.offscreenCanvas.width = canvas.width;
    this.offscreenCanvas.height = canvas.height;
    this.offscreenCtx = this.offscreenCanvas.getContext('2d')!;
  }
  
  render(candidates: RadarCandidate[]) {
    if (!this.needsRedraw) return;
    
    // Cancel previous frame
    if (this.frameRequest) {
      cancelAnimationFrame(this.frameRequest);
    }
    
    this.frameRequest = requestAnimationFrame(() => {
      // Render to offscreen canvas
      this.renderOffscreen(candidates);
      
      // Copy to main canvas
      this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
      this.ctx.drawImage(this.offscreenCanvas, 0, 0);
      
      this.needsRedraw = false;
    });
  }
  
  private renderOffscreen(candidates: RadarCandidate[]) {
    // Sort by z-index (selected/hovered on top)
    const sorted = [...candidates].sort((a, b) => {
      if (a.selected) return 1;
      if (b.selected) return -1;
      if (a.hovered) return 1;
      if (b.hovered) return -1;
      return 0;
    });
    
    // Batch similar operations
    this.offscreenCtx.save();
    
    // Draw all regular candidates first
    sorted.filter(c => !c.selected && !c.hovered).forEach(candidate => {
      this.drawCandidate(candidate, false);
    });
    
    // Draw highlighted candidates last
    sorted.filter(c => c.selected || c.hovered).forEach(candidate => {
      this.drawCandidate(candidate, true);
    });
    
    this.offscreenCtx.restore();
  }
}
```

### Level of Detail (LOD)

```typescript
class LODRenderer {
  private zoomLevels = {
    far: 0.5,
    medium: 1.0,
    close: 2.0
  };
  
  drawCandidateWithLOD(
    candidate: RadarCandidate,
    zoom: number,
    centerX: number,
    centerY: number
  ) {
    const distanceFromCenter = Math.sqrt(
      (candidate.x - centerX) ** 2 + 
      (candidate.y - centerY) ** 2
    );
    
    // Determine LOD based on zoom and distance
    let lod: 'high' | 'medium' | 'low';
    
    if (zoom > this.zoomLevels.close || distanceFromCenter < 100) {
      lod = 'high';
    } else if (zoom > this.zoomLevels.medium || distanceFromCenter < 200) {
      lod = 'medium';
    } else {
      lod = 'low';
    }
    
    switch (lod) {
      case 'high':
        // Full detail - draw everything
        this.drawFullCandidate(candidate);
        this.drawCandidateLabel(candidate);
        this.drawSkillBadges(candidate);
        break;
        
      case 'medium':
        // Medium detail - basic info
        this.drawFullCandidate(candidate);
        if (candidate.hovered) {
          this.drawCandidateLabel(candidate);
        }
        break;
        
      case 'low':
        // Low detail - just dot
        this.drawSimpleDot(candidate);
        break;
    }
  }
  
  private drawSimpleDot(candidate: RadarCandidate) {
    this.ctx.beginPath();
    this.ctx.fillStyle = candidate.color;
    this.ctx.arc(candidate.x, candidate.y, 4, 0, Math.PI * 2);
    this.ctx.fill();
  }
}
```

## Real-World Examples

### Example Usage

```typescript
// Initialize radar
const radar = new TalentRadar({
  container: document.getElementById('talent-radar'),
  width: 800,
  height: 600,
  interactive: true,
  showLabels: true,
  clustering: true
});

// Load search results
const searchResults = await searchCandidates('Python developer with AWS');

// Transform and display
const radarCandidates = searchResults.map(result => ({
  id: result.id,
  name: `${result.first_name} ${result.last_name}`,
  title: result.current_title,
  score: result.score,
  availability: result.availability_score,
  experience: result.years_experience,
  skills: result.skills
}));

radar.setCandidates(radarCandidates);

// Handle selection
radar.onCandidateSelect = (candidate) => {
  showCandidateDetails(candidate);
};

// Animate entrance
radar.animateIn();
```

### Custom Styling

```typescript
const customRadar = new TalentRadar({
  theme: {
    background: '#1a1a1a',
    gridColor: '#333333',
    textColor: '#ffffff',
    candidateColors: {
      available: '#4ade80',
      maybe: '#fb923c', 
      unavailable: '#f87171'
    },
    glowEffect: true,
    particleEffect: true
  },
  physics: {
    repulsion: 150,
    attraction: 0.05,
    damping: 0.85
  }
});
```

## Future Enhancements

### 1. 3D Visualization

```typescript
class Radar3D {
  private scene: THREE.Scene;
  private camera: THREE.PerspectiveCamera;
  private renderer: THREE.WebGLRenderer;
  
  initialize() {
    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(
      75,
      window.innerWidth / window.innerHeight,
      0.1,
      1000
    );
    
    this.renderer = new THREE.WebGLRenderer({ antialias: true });
    
    // Add candidates as 3D spheres
    this.candidates.forEach(candidate => {
      const geometry = new THREE.SphereGeometry(candidate.radius / 100);
      const material = new THREE.MeshPhongMaterial({
        color: candidate.color,
        emissive: candidate.color,
        emissiveIntensity: 0.2
      });
      
      const sphere = new THREE.Mesh(geometry, material);
      sphere.position.set(
        candidate.x / 100,
        candidate.y / 100,
        candidate.score * 50
      );
      
      this.scene.add(sphere);
    });
  }
}
```

### 2. AI-Powered Insights

```typescript
class RadarAIInsights {
  async analyzeRadarPattern(candidates: RadarCandidate[]) {
    const clusters = this.identifyClusters(candidates);
    
    const insights = await this.ai.analyze({
      clusters,
      distribution: this.calculateDistribution(candidates),
      gaps: this.findTalentGaps(candidates)
    });
    
    return {
      summary: insights.summary,
      recommendations: insights.recommendations,
      hiddenGems: this.findHiddenGems(candidates),
      teamComposition: this.analyzeTeamFit(candidates)
    };
  }
  
  private findHiddenGems(candidates: RadarCandidate[]): RadarCandidate[] {
    // Find high-potential candidates in outer rings
    return candidates.filter(c => 
      c.distance > 0.6 && // Outer ring
      c.availability > 0.8 && // High availability
      c.experience > 5 // Experienced
    );
  }
}
```

### 3. Real-Time Collaboration

```typescript
class CollaborativeRadar {
  private websocket: WebSocket;
  private collaborators: Map<string, Collaborator> = new Map();
  
  connectToSession(sessionId: string) {
    this.websocket = new WebSocket(`wss://api/radar/${sessionId}`);
    
    this.websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      switch (data.type) {
        case 'collaborator-joined':
          this.addCollaborator(data.collaborator);
          break;
          
        case 'candidate-selected':
          this.highlightCandidate(data.candidateId, data.collaboratorId);
          break;
          
        case 'annotation-added':
          this.addAnnotation(data.annotation);
          break;
      }
    };
  }
  
  private addCollaborator(collaborator: Collaborator) {
    this.collaborators.set(collaborator.id, collaborator);
    
    // Show collaborator cursor
    this.showCollaboratorCursor(collaborator);
  }
}
```

The Smart Talent Radar transforms complex candidate data into an intuitive visual experience, making it easy to identify the best matches and understand your talent landscape at a glance.