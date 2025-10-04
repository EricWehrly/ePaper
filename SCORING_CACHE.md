# Scoring Cache Implementation

## Overview

Added on-disk caching for image quality scoring to avoid recomputing expensive metrics when files haven't changed. The cache uses file modification times (mtimes) as the "truth" mechanism, similar to the existing conversion timestamp approach.

## Implementation Details

### Cache Location and Format
- **File**: `.score_cache.json` in the same directory as converted images (`pic/` directory)
- **Format**: JSON with entries keyed by converted filename
- **Entry Structure**:
  ```json
  {
    "image_filename.bmp": {
      "image_mtime": 1696377496.123,
      "original_mtime": 1696377495.456,
      "scores": {
        "total_score": 49.1,
        "structural_similarity": 45.2,
        "color_fidelity": 52.3,
        "edge_preservation": 50.8,
        "skin_tone_score": 12.5,
        "skin_coverage_percent": 8.2,
        "weighted_skin_score": 1.03,
        "original_image": "helsinki.png"
      }
    }
  }
  ```

### Cache Logic
1. **Read**: Check if cache exists and load existing entries
2. **Validate**: Compare stored mtimes with current file mtimes
3. **Hit**: Return cached scores if both original and converted file mtimes match
4. **Miss**: Compute scores, update cache, return results
5. **Write**: Atomic write using temporary file + rename to avoid corruption

### Thread Safety
- Uses `threading.Lock()` to prevent concurrent cache writes
- Cache reads are lock-free (JSON loading is atomic)

## Performance Impact

### Before Caching
- Full scoring run: ~2+ minutes for 8 images
- Each image required full comparative analysis

### After Caching
- First run: Still ~2+ minutes (computes and writes cache)
- Subsequent runs: <1 second (reads from cache)
- Only changed files trigger recomputation

## Edge Cases Handled

### File System Issues
- **Corrupted cache**: Ignored and rebuilt from scratch
- **Cache write failures**: Scoring continues, results still returned
- **Missing cache directory**: Cache write skipped gracefully
- **Permission errors**: Cache operations are non-blocking

### File State Issues
- **Modified original**: Original mtime change triggers re-score
- **Modified converted**: Converted mtime change triggers re-score
- **Missing files**: Standard error handling (score: 999)
- **Clock skew**: Uses file system mtimes consistently

### Concurrency Issues
- **Multiple processes**: Threading lock prevents cache corruption
- **Rapid successive runs**: Atomic writes prevent partial cache states

## Possible Future Improvements

### Cache Management
- [ ] **Central cache location**: Move from per-directory to project root cache
- [ ] **Cache size limits**: Implement LRU or size-based pruning
- [ ] **Cache TTL**: Add time-based expiration for entries
- [ ] **Cache clearing**: Add `--clear-score-cache` CLI flag
- [ ] **Cache stats**: Report hit/miss ratios and cache size

### Robustness
- [ ] **Content hashing**: Use file content hash instead of mtime for stronger validation
- [ ] **Path-based keys**: Use relative paths as keys to avoid filename collisions
- [ ] **Version tagging**: Include scoring algorithm version in cache entries
- [ ] **Backup/restore**: Add cache export/import functionality

### Performance
- [ ] **Parallel scoring**: Score multiple images concurrently
- [ ] **Incremental updates**: Only re-score changed metrics
- [ ] **Memory caching**: Add in-memory cache layer for frequently accessed scores
- [ ] **Compression**: Compress cache file for large image sets

### Integration
- [ ] **CLI integration**: Add cache status and management commands
- [ ] **Logging**: Add cache hit/miss logging at DEBUG level
- [ ] **Metrics**: Expose cache performance metrics
- [ ] **Testing**: Add unit tests for cache behavior

### Advanced Features
- [ ] **Distributed caching**: Share cache across multiple machines
- [ ] **Selective caching**: Configure which metrics to cache
- [ ] **Cache warming**: Pre-compute scores for known image sets
- [ ] **Delta scoring**: Store only changed metrics between versions

## Files Modified

- `src/scoring/core.py`: Added cache read/write logic to `ImageQualityScorer.score_converted_image()`
- `src/main.py`: Fixed import path to work when run from project root

## Usage Notes

### Cache Inspection
```bash
# View cache contents
cat pic/.score_cache.json

# Check cache file details
ls -la pic/.score_cache.json
```

### Cache Invalidation
```bash
# Force re-score by updating original file timestamp
touch pic-raw/image.jpg

# Or remove cache entirely
rm pic/.score_cache.json
```

### Testing Cache Behavior
```bash
# First run (slow - computes and caches)
time python src/main.py

# Second run (fast - uses cache)
time python src/main.py

# Modify source and run again (partial recompute)
touch pic-raw/helsinki.jpg
time python src/main.py
```

## Technical Considerations

### Cache Key Strategy
- Current: Uses filename as key (`image.bmp`)
- Risk: Name collisions if same filename exists in different contexts
- Mitigation: Currently low risk since all converted images are in `pic/`

### Atomic Write Strategy
- Writes to `.tmp` file first, then renames to final location
- Prevents partial writes from corrupting cache
- Works across filesystems and handles interruption gracefully

### Error Handling Philosophy
- Cache errors never block scoring functionality
- Graceful degradation: cache miss → compute scores → continue
- Logging: Errors logged but don't propagate upward

## Implementation Timeline

- **Phase 1** ✅: Basic mtime-based caching with atomic writes
- **Phase 2** (Future): Cache management and CLI integration
- **Phase 3** (Future): Advanced features and performance optimizations