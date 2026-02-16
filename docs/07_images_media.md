# Images & Media Handling

Images handling:

- Images are uploaded via seller endpoints
- Stored on disk (static/uploads or storage/)
- DB stores image paths only

Why?
- DB should not store heavy files
- Filesystem is cheaper and faster

Flow:
Upload → Validate → Save → Return URL

