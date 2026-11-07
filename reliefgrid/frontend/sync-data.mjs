// The disconnected map preview is generated from the backend's canonical data.
import {copyFile} from 'node:fs/promises';
await copyFile(new URL('../scenarios/riverbend.json',import.meta.url),new URL('./src/offline-scenario.json',import.meta.url));
await copyFile(new URL('../scenarios/background.geojson',import.meta.url),new URL('./src/background.json',import.meta.url));
