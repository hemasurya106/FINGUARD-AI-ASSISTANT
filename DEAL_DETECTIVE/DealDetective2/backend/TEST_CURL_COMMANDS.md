# Curl Commands to Test DealDetective API

## 1. Test Root Endpoint
```bash
curl http://127.0.0.1:8000/
```

## 2. Test Health Check
```bash
curl http://127.0.0.1:8000/health
```

## 3. Test Analyze Input with URL (Amazon example)
```bash
curl -X POST "http://127.0.0.1:8000/analyze-input" \
  -F "https://www.amazon.in/dp/B0FGDP9LW4/ref=sspa_dk_detail_4?psc=1&pd_rd_i=B0FGDP9LW4&pd_rd_w=U5Eaq&content-id=amzn1.sym.67d3dec9-3503-44a1-a945-e969d04cca69&pf_rd_p=67d3dec9-3503-44a1-a945-e969d04cca69&pf_rd_r=86SFEPWDEEAZ6NC69PT6&pd_rd_wg=CLWVy&pd_rd_r=4efb2786-4bbd-4081-942d-3c82bba621af&aref=dp5IX0UY1I&sp_csd=d2lkZ2V0TmFtZT1zcF9kZXRhaWxfdGhlbWF0aWM"
```

## 4. Test Analyze Input with URL (Any product URL)
```bash
curl -X POST "http://127.0.0.1:8000/analyze-input" \
  -F "url=https://example.com/product"
```

## 5. Test Analyze Input with Image Upload
```bash
curl -X POST "http://127.0.0.1:8000/analyze-input" \
  -F "image=@/path/to/your/image.jpg"
```

## 6. Test with Product Name (if supported)
```bash
curl -X POST "http://127.0.0.1:8000/analyze-input" \
  -F "product_name=iPhone 15 Pro"
```

## 7. Pretty Print JSON Response
```bash
curl -X POST "http://127.0.0.1:8000/analyze-input" \
  -F "url=https://www.amazon.in/dp/B08XYZ1234" | jq
```

## 8. Verbose Output (see headers and response)
```bash
curl -v -X POST "http://127.0.0.1:8000/analyze-input" \
  -F "url=https://www.amazon.in/dp/B08XYZ1234"
```

