## Buat Tamnel

```
ffmpeg -i input.jpg -vf "scale=480:-1:flags=lanczos" -c:v libwebp -quality 88 -compression_level 6 thumbnail.webp
```
