# Electron Desktop App Setup

## المشروع دلوقتي
- Frontend: React + TypeScript + Vite + Shadcn UI
- Desktop: Electron
- Backend: هيتعمل لاحقاً بـ Go + Python

## Commands

### Development (تشغيل الـ app كـ desktop)
```bash
bun run electron:dev
```
ده هيشغل Vite dev server + Electron window مع hot reload

### Build للـ Production
```bash
bun run electron:build:win
```
ده هيبني الـ app كـ Windows installer (.exe) في مجلد `release/`

### Web Development فقط (بدون Electron)
```bash
bun run dev
```
ده هيشغل Vite dev server عادي على http://localhost:8080

## الخطوات الجاية

1. **Frontend**: كمل بناء الـ UI بتاعك
2. **Backend**: 
   - اعمل Go server للـ APIs
   - اعمل Python scripts للـ processing
3. **Integration**: 
   - اربط الـ Electron بالـ backend عن طريق `electron/main.js`
   - استخدم IPC (Inter-Process Communication) للتواصل بين Frontend و Backend
   - عدل `electron/preload.js` عشان تعرض APIs للـ frontend

## ملفات مهمة

- `electron/main.js` - الـ Electron main process (هنا هتشغل الـ backend servers)
- `electron/preload.js` - الـ bridge بين Frontend و Backend
- `src/types/electron.d.ts` - TypeScript types للـ Electron APIs
- `package.json` - فيه الـ build configuration

## Notes

- الـ app دلوقتي بيشتغل كـ desktop application
- في Development mode بيحمل من Vite dev server
- في Production بيحمل من الملفات المبنية في `dist/`
