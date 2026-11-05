## Membuat Thumbnail

```
ffmpeg -i input.jpg -vf "scale=320:-1:flags=lanczos" -frames:v 1 -c:v libwebp -quality 45 -compression_level 6 -preset photo -an thumbnail.webp
```
