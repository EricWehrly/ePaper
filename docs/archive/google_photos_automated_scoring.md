# Automated Photo Scoring with Google Photos API

## Overview

Analysis of how to implement automated photo scoring and selection within the constraints of Google Photos API (post-March 2025). While full library trawling is not possible, we can achieve effective semi-automated curation.

---

## API Constraints Summary

### What We CANNOT Do ❌
- **Automatic library scanning**: No background access to user's photo library
- **Programmatic browsing**: Cannot iterate through albums or photos without user selection  
- **Silent photo access**: Every photo requires explicit user consent via Picker API
- **Scheduled imports**: Cannot automatically check for new photos

### What We CAN Do ✅
- **Batch processing**: Score large sets of user-selected photos
- **Smart filtering**: Analyze selections and recommend best candidates
- **Pattern learning**: Track user preferences over time
- **Guided selection**: Help users choose optimal photo sets

---

## Recommended Implementation: Batch Score & Filter

### Architecture Overview

```
User Selection (Google Photos) 
    ↓
Batch Download (50-100 photos)
    ↓  
Parallel Scoring Pipeline
    ↓
Ranking & Recommendation Engine
    ↓
User Review & Selection
    ↓
E-Paper Display Queue
```

### Technical Implementation

#### 1. Enhanced Picker Integration
```python
# src/google_photos/batch_processor.py

class BatchPhotoProcessor:
    def __init__(self, scoring_engine, max_batch_size=100):
        self.scoring_engine = scoring_engine
        self.max_batch_size = max_batch_size
        
    async def process_selection(self, session_id: str) -> List[ScoredPhoto]:
        """Process all photos from a picker session with scoring."""
        
        # Get all selected media items
        picker = GooglePhotosPicker(self.credentials)
        media_items = picker.list_media_items(session_id)
        
        if len(media_items) > self.max_batch_size:
            # Offer to process in chunks or ask user to refine selection
            return await self.handle_large_batch(media_items)
            
        # Download and score in parallel
        scored_photos = await self.download_and_score_batch(media_items)
        
        # Rank by e-paper suitability 
        ranked_photos = self.rank_photos_for_epaper(scored_photos)
        
        return ranked_photos
        
    async def download_and_score_batch(self, media_items: List[Dict]) -> List[ScoredPhoto]:
        """Download and score photos in parallel."""
        tasks = []
        
        for item in media_items:
            task = asyncio.create_task(self.download_and_score_single(item))
            tasks.append(task)
            
        # Process with controlled concurrency (respect rate limits)
        semaphore = asyncio.Semaphore(5)  # Max 5 concurrent downloads
        
        async def bounded_task(task):
            async with semaphore:
                return await task
                
        results = await asyncio.gather(
            *[bounded_task(task) for task in tasks],
            return_exceptions=True
        )
        
        # Filter out failures
        return [r for r in results if isinstance(r, ScoredPhoto)]
        
    async def download_and_score_single(self, media_item: Dict) -> ScoredPhoto:
        """Download single photo and run full scoring pipeline."""
        
        # Download photo
        downloader = GooglePhotosDownloader(self.credentials)
        local_path = await downloader.download_media_item_async(media_item)
        
        if not local_path:
            raise Exception(f"Failed to download {media_item.get('id')}")
            
        try:
            # Run through existing scoring system
            from src.scoring.core import PhotoScorer
            scorer = PhotoScorer()
            
            score_results = scorer.score_image(local_path)
            
            return ScoredPhoto(
                media_item=media_item,
                local_path=local_path,
                scores=score_results,
                epaper_suitability=self.calculate_epaper_score(score_results)
            )
            
        except Exception as e:
            logger.error(f"Scoring failed for {local_path}: {e}")
            # Return with minimal score data
            return ScoredPhoto(
                media_item=media_item,
                local_path=local_path,
                scores=None,
                epaper_suitability=0.0
            )
            
    def calculate_epaper_score(self, score_results: Dict) -> float:
        """Calculate composite e-paper suitability score."""
        
        if not score_results:
            return 0.0
            
        # Weight factors for e-paper display
        weights = {
            'contrast': 0.3,      # High contrast works well on e-paper
            'edge_density': 0.25, # Clear edges are important  
            'color_palette': 0.2, # How well it converts to 6-color
            'composition': 0.15,  # Rule of thirds, etc.
            'skin_detection': -0.1 # Penalize photos with large skin areas (don't convert well)
        }
        
        epaper_score = 0.0
        
        for factor, weight in weights.items():
            if factor in score_results:
                normalized_score = score_results[factor] / 100.0  # Normalize to 0-1
                epaper_score += normalized_score * weight
                
        # Ensure score stays in 0-1 range
        return max(0.0, min(1.0, epaper_score))
        
    def rank_photos_for_epaper(self, scored_photos: List[ScoredPhoto]) -> List[ScoredPhoto]:
        """Rank photos by e-paper suitability."""
        return sorted(scored_photos, key=lambda p: p.epaper_suitability, reverse=True)
```

#### 2. Smart Recommendation Engine
```python
# src/google_photos/recommendation_engine.py

class RecommendationEngine:
    def __init__(self, db_connection):
        self.db = db_connection
        
    def generate_recommendations(self, scored_photos: List[ScoredPhoto], user_id: str) -> Dict:
        """Generate smart recommendations based on scoring and user history."""
        
        # Get user's historical preferences
        user_prefs = self.get_user_preferences(user_id)
        
        # Basic recommendations
        recommendations = {
            'top_technical': scored_photos[:5],  # Top 5 by technical score
            'high_contrast': self.filter_by_contrast(scored_photos, threshold=0.7),
            'good_edges': self.filter_by_edges(scored_photos, threshold=0.6),
            'color_friendly': self.filter_by_color_conversion(scored_photos),
        }
        
        # Personalized recommendations if we have history
        if user_prefs:
            recommendations['personalized'] = self.apply_user_preferences(
                scored_photos, user_prefs
            )
            
        # Diversity recommendations (avoid too similar photos)
        recommendations['diverse_set'] = self.select_diverse_photos(
            scored_photos, count=10
        )
        
        return recommendations
        
    def get_user_preferences(self, user_id: str) -> Dict:
        """Learn from user's past selections."""
        
        # Query database for photos user actually displayed
        query = """
        SELECT scoring_data, user_rating 
        FROM displayed_photos 
        WHERE user_id = ? AND user_rating > 0
        ORDER BY created_at DESC 
        LIMIT 100
        """
        
        history = self.db.execute(query, (user_id,)).fetchall()
        
        if not history:
            return None
            
        # Analyze patterns in what user actually likes
        preferences = {
            'preferred_contrast_range': self.analyze_contrast_preferences(history),
            'color_preferences': self.analyze_color_preferences(history),
            'composition_preferences': self.analyze_composition_preferences(history),
            'subject_preferences': self.analyze_subject_preferences(history)
        }
        
        return preferences
        
    def select_diverse_photos(self, scored_photos: List[ScoredPhoto], count: int) -> List[ScoredPhoto]:
        """Select diverse set of high-quality photos (avoid too many similar ones)."""
        
        selected = []
        remaining = scored_photos.copy()
        
        while len(selected) < count and remaining:
            # Take the highest scored remaining photo
            best = remaining.pop(0)
            selected.append(best)
            
            # Remove photos that are too similar to this one
            remaining = self.filter_similar_photos(remaining, best, threshold=0.8)
            
        return selected
        
    def filter_similar_photos(self, photos: List[ScoredPhoto], reference: ScoredPhoto, threshold: float) -> List[ScoredPhoto]:
        """Remove photos that are too similar to reference photo."""
        
        filtered = []
        
        for photo in photos:
            similarity = self.calculate_photo_similarity(photo, reference)
            if similarity < threshold:
                filtered.append(photo)
                
        return filtered
        
    def calculate_photo_similarity(self, photo1: ScoredPhoto, photo2: ScoredPhoto) -> float:
        """Calculate similarity between two photos based on visual features."""
        
        # Simple similarity based on scoring features
        # Could be enhanced with perceptual hashing, etc.
        
        if not (photo1.scores and photo2.scores):
            return 0.0
            
        features = ['contrast', 'edge_density', 'color_palette', 'composition']
        
        differences = []
        for feature in features:
            if feature in photo1.scores and feature in photo2.scores:
                diff = abs(photo1.scores[feature] - photo2.scores[feature]) / 100.0
                differences.append(diff)
                
        if not differences:
            return 0.0
            
        # Average difference (0 = identical, 1 = completely different)
        avg_diff = sum(differences) / len(differences)
        
        # Convert to similarity (0 = different, 1 = similar)
        return 1.0 - avg_diff
```

#### 3. User Interface for Batch Processing
```python
# src/web/routes.py - Enhanced routes

@app.route('/api/google-photos/batch-process/<session_id>', methods=['POST'])
def batch_process_session(session_id):
    """Process entire photo selection with scoring and recommendations."""
    
    try:
        processor = BatchPhotoProcessor(scoring_engine=app.scoring_engine)
        scored_photos = await processor.process_selection(session_id)
        
        # Generate recommendations
        recommender = RecommendationEngine(app.db)
        recommendations = recommender.generate_recommendations(
            scored_photos, 
            session.get('user_id', 'anonymous')
        )
        
        return jsonify({
            'total_photos': len(scored_photos),
            'processing_time': processor.last_processing_time,
            'recommendations': {
                'top_picks': [p.to_dict() for p in recommendations['top_technical'][:3]],
                'high_contrast': [p.to_dict() for p in recommendations['high_contrast'][:3]], 
                'diverse_selection': [p.to_dict() for p in recommendations['diverse_set'][:5]]
            },
            'all_results': [p.to_dict() for p in scored_photos[:20]]  # Limit for UI
        })
        
    except Exception as e:
        logger.error(f"Batch processing failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/google-photos/recommendations/<session_id>')  
def get_detailed_recommendations(session_id):
    """Get detailed recommendations with explanations."""
    
    # Retrieve cached processing results
    results = app.cache.get(f"batch_results_{session_id}")
    if not results:
        return jsonify({'error': 'Session results not found'}), 404
        
    recommendations = results['recommendations']
    
    # Add explanations for each recommendation
    explained_recs = {}
    for category, photos in recommendations.items():
        explained_recs[category] = {
            'photos': [p.to_dict() for p in photos],
            'explanation': get_recommendation_explanation(category),
            'count': len(photos)
        }
        
    return jsonify(explained_recs)

def get_recommendation_explanation(category: str) -> str:
    """Provide user-friendly explanations for recommendation categories."""
    
    explanations = {
        'top_technical': "These photos scored highest on technical quality metrics like contrast and edge definition.",
        'high_contrast': "These photos have strong contrast that will look great on the e-paper display.",
        'color_friendly': "These photos convert well to the 6-color e-paper palette.",
        'diverse_set': "A varied selection of your best photos to avoid too many similar images.",
        'personalized': "Based on your past photo preferences and display history."
    }
    
    return explanations.get(category, "Recommended based on e-paper display optimization.")
```

---

## Integration with Existing Scoring System

### Leverage Current Infrastructure

Your existing scoring system in `src/scoring/` can be directly integrated:

```python
# Enhanced integration example
from src.scoring.core import PhotoScorer
from src.scoring.color import ColorAnalyzer  
from src.scoring.edges import EdgeDetector
from src.scoring.structure import CompositionAnalyzer

class EPaperOptimizedScorer(PhotoScorer):
    """Extended scorer optimized for e-paper display selection."""
    
    def __init__(self):
        super().__init__()
        self.epaper_weights = {
            'contrast': 0.35,
            'edge_quality': 0.30, 
            'color_conversion': 0.20,
            'composition': 0.15
        }
        
    def score_for_epaper(self, image_path: str) -> Dict:
        """Score image specifically for e-paper suitability."""
        
        # Run standard scoring
        base_scores = self.score_image(image_path)
        
        # Add e-paper specific evaluations
        epaper_scores = self.evaluate_epaper_factors(image_path)
        
        # Combine scores
        combined_scores = {**base_scores, **epaper_scores}
        
        # Calculate weighted e-paper suitability
        suitability = self.calculate_epaper_suitability(combined_scores)
        
        return {
            'base_scores': base_scores,
            'epaper_scores': epaper_scores,
            'epaper_suitability': suitability,
            'recommendation': self.get_recommendation(suitability)
        }
        
    def evaluate_epaper_factors(self, image_path: str) -> Dict:
        """Evaluate factors specific to e-paper display."""
        
        # Load image
        image = cv2.imread(image_path)
        
        scores = {}
        
        # E-paper color conversion quality
        scores['color_conversion_quality'] = self.test_6color_conversion(image)
        
        # Text readability (if image contains text)
        scores['text_readability'] = self.evaluate_text_clarity(image)
        
        # Dithering suitability
        scores['dithering_friendly'] = self.evaluate_dithering_potential(image)
        
        # Size optimization potential  
        scores['resize_quality'] = self.test_resize_to_epaper_resolution(image)
        
        return scores
```

---

## User Experience Design

### Batch Processing UI Flow

1. **Selection Phase**
   - "Select 20-50 photos for smart analysis"
   - Progress indicator during download
   - "Analyzing photos for e-paper suitability..."

2. **Results Phase**  
   - "Here are your top recommendations:"
   - Visual grid with scores and explanations
   - "Why this photo?" tooltips

3. **Refinement Phase**
   - "Add to display queue" buttons
   - "Show me more like this" options
   - "Not interested in photos like this" feedback

### Example UI Messages

```
🎯 Smart Analysis Complete!
   Processed 47 photos in 23 seconds

⭐ Top Recommendations:
   • sunset_beach.jpg - Excellent contrast and color conversion
   • family_portrait.jpg - Sharp edges, good composition  
   • mountain_view.jpg - High detail, minimal skin tones

📊 All Results: 
   • 12 photos rated "Excellent" for e-paper
   • 23 photos rated "Good" 
   • 12 photos rated "Fair"

💡 Tips: Photos with high contrast and clear subjects work best on e-paper displays.
```

---

## Conclusion

While true "automated trawling" isn't possible due to API restrictions, the batch processing + smart recommendation approach can achieve very similar results:

- **User selects large batches** (50-100 photos at once)
- **System automatically scores and ranks** all selections
- **Smart recommendations** surface the best e-paper candidates
- **Learning system** improves recommendations over time

This provides the automation you want while respecting Google's API constraints and user privacy controls.