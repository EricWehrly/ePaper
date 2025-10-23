# Google Photos API Feasibility Study

## Executive Summary

After comprehensive research into Google Photos APIs (as of October 2025), we have **good news**: Google's recent changes have actually made photo selection more viable, not less. The new **Picker API** is specifically designed for our use case and provides a secure, user-friendly way to integrate Google Photos with external applications.

**Bottom Line**: Integration is definitely feasible, though it requires a different approach than traditional file browsing. Users will select photos through Google's official interface, which then provides our app with download access.

---

## Current API Landscape (October 2025)

### Major Changes in March 2025

Google significantly restructured their Photos APIs in March 2025:

1. **Introduced** the new **Picker API** - specifically for photo selection use cases
2. **Restricted** the Library API to only work with app-created content
3. **Removed** broad library access scopes that enabled full photo browsing

### Two APIs Available

1. **Picker API** - For selecting and downloading existing user photos ✅ **(Our use case)**
2. **Library API** - For managing photos/albums created by your app only

---

## Picker API Analysis

### What It Provides ✅

**Core Functionality**:
- Secure photo selection through Google's native interface
- Access to selected photos with full resolution downloads
- Support for images and videos
- Built-in search capabilities (dates, keywords, locations, albums)
- User maintains full control over what they share

**Technical Access**:
- Full resolution image downloads (up to 16,383px dimensions)
- Multiple format options (JPEG, PNG, etc.)
- Flexible sizing with aspect ratio preservation
- Cropping options for exact dimensions
- Metadata access (minus location data for privacy)
- Video downloads in high-quality transcoded format

### User Experience Flow

1. **App creates session** → Gets a `pickerUri`
2. **User clicks link/scans QR** → Opens Google Photos app
3. **User searches & selects** → Built-in Google Photos interface
4. **User hits "Done"** → Selection complete
5. **App polls session** → Checks for completion
6. **App downloads selected images** → Using provided URLs

### What It Doesn't Provide ❌

**No Custom UI**:
- Cannot embed Google Photos browser in iframe/modal
- Cannot create custom photo browsing interface
- Must use Google's selection UI (actually a benefit for UX/security)

**No Background Access**:
- Cannot auto-sync or monitor user's library
- Cannot access photos without explicit user selection
- Each selection session requires user interaction

---

## Technical Requirements

### Authentication
- **OAuth 2.0** with `photospicker.mediaitems.readonly` scope
- **No service accounts** - requires user login
- **Verification required** if app becomes public
- Standard web or mobile OAuth flows supported

### API Limits
- **10,000 API requests/day** (creating sessions, listing selections)
- **75,000 media downloads/day** (actual image downloads)
- **60-minute expiry** on download URLs
- Rate limiting protections (429 errors if exceeded)

### Integration Complexity
- **Medium complexity** - straightforward REST API
- **Cross-origin considerations** for web apps
- **Mobile-friendly** - works well on phones/tablets
- **QR code fallback** for cross-device scenarios

---

## Feasibility Assessment

### ✅ Pros

1. **Perfect for Our Use Case**
   - Designed exactly for "let users pick photos from Google Photos"
   - Secure, privacy-focused approach
   - Full resolution access to selected images

2. **User Experience Benefits**
   - Familiar Google Photos interface
   - Built-in search is better than anything we could build
   - Users trust Google's security model
   - Works across devices (QR codes)

3. **Technical Advantages**
   - Well-documented, modern API
   - Reasonable rate limits for personal use
   - Flexible image sizing/cropping options
   - Active support and development from Google

4. **Integration Friendly**
   - RESTful API, works with any backend language
   - Can integrate with our existing Flask web interface
   - Supports both web and mobile flows

### ⚠️ Challenges

1. **UX Flow Considerations**
   - Users leave our app to select photos (unavoidable)
   - Requires extra steps vs. local file upload
   - Need to educate users about the flow

2. **Technical Limitations**
   - Cannot pre-browse or cache user's library
   - Each selection requires new session
   - Download URLs expire after 60 minutes

3. **Dependencies**
   - Relies on Google's service availability
   - Subject to future API changes
   - Requires internet connectivity

### ❌ Show Stoppers: None Identified

The API provides everything needed for our core use case.

---

## Comparison with Alternatives

### vs. Local File Upload
- **Google Photos**: Better for mobile users, leverages existing photo library
- **Local Upload**: Simpler flow but requires manual file management

### vs. Other Cloud Services
- **Google Photos**: Largest user base, best integration support
- **iCloud, Dropbox, etc.**: More limited APIs, smaller user base

### vs. Manual Download/Upload
- **Google Photos API**: Seamless integration, no double work
- **Manual**: Clunky user experience, extra steps

---

## Risk Assessment

### Low Risks ✅
- API stability (new, actively developed)
- Rate limits (generous for personal use)
- Technical complexity (well documented)

### Medium Risks ⚠️
- User adoption (requires education about flow)
- Future API changes (Google's track record is mixed)
- OAuth verification requirements for public apps

### High Risks ❌
- None identified for personal/small-scale use

---

## Conclusion

**Recommendation: Proceed with Integration**

The Google Photos Picker API is not only feasible but well-suited for our e-paper display project. While it doesn't provide the "browse photos in a modal" experience initially desired, it offers something better: a secure, user-friendly way to select photos using Google's own interface.

**Key Success Factors:**
1. Focus on the UX flow education (show users what to expect)
2. Start with simple single-photo selection
3. Build robust error handling for network issues
4. Consider fallback to local upload for users without Google Photos

The recent API changes eliminated concerns about Google "destroying" the API - they've actually improved it for legitimate use cases like ours.

---

*Research completed: October 2025*  
*APIs covered: Google Photos Picker API v1, Library API v1*  
*Documentation reviewed: Official Google Developer docs, recent policy changes*