# Vercel Deployment Size Fix

## Problem

Your Vercel deployment was failing with the error:

```
Error: A Serverless Function has exceeded the unzipped maximum size of 250 MB.
```

## Root Cause

The issue was caused by large binary dependencies, particularly:

- **PyMuPDF** (fitz) with its large DLL files (~20MB each)
- **Large data files** in data directories
- **Development files** and caches

## Solution Implemented

### 1. Created `.vercelignore` File

- Excludes large binary files (_.dll, _.pyd, \*.so)
- Excludes data directories and large files
- Excludes development and cache files

### 2. Created `requirements-vercel.txt`

- Optimized dependency list for deployment
- Removed PyMuPDF (large binary dependency)
- Kept essential packages only

### 3. Updated `vercel.json`

- Added custom install command to use optimized requirements
- Configured proper build settings

### 4. Modified Contract Review Endpoint

- Added conditional import for PyMuPDF
- Implemented fallback to pypdf for text extraction
- Maintains functionality while reducing size

### 5. Created Build Script

- `build-vercel.py` for automated cleanup
- Removes large files before deployment
- Optimizes project structure

## Files Modified/Created

### New Files:

- `.vercelignore` - Excludes large files from deployment
- `requirements-vercel.txt` - Optimized dependencies
- `build-vercel.py` - Build optimization script
- `VERCEL_DEPLOYMENT_FIX.md` - This documentation

### Modified Files:

- `vercel.json` - Updated build configuration
- `endpoints/contract_review.py` - Added PyMuPDF fallback

## Deployment Steps

1. **Run the build script** (optional but recommended):

   ```bash
   python build-vercel.py
   ```

2. **Commit your changes**:

   ```bash
   git add .
   git commit -m "Fix Vercel deployment size limit"
   git push origin development
   ```

3. **Redeploy on Vercel**:
   - Go to your Vercel dashboard
   - Trigger a new deployment
   - The deployment should now succeed

## Expected Results

- **Bundle size**: Reduced from >250MB to <100MB
- **Functionality**: Maintained with fallback mechanisms
- **Performance**: Faster cold starts due to smaller bundle

## Fallback Behavior

When PyMuPDF is not available (in Vercel deployment):

- PDF text extraction still works using pypdf
- Form field extraction is disabled (returns empty dict)
- All other functionality remains intact

## Monitoring

After deployment, monitor:

- Function execution time
- Memory usage
- Error rates
- Cold start performance

## Rollback Plan

If issues occur:

1. Revert to original `requirements.txt`
2. Remove `.vercelignore`
3. Restore original `vercel.json`
4. Redeploy

## Additional Optimizations

For further size reduction:

1. Consider using external PDF processing services
2. Implement lazy loading for heavy dependencies
3. Use Vercel's Edge Functions for lightweight operations
4. Consider splitting into multiple smaller functions
