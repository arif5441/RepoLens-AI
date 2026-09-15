import '@ui5/webcomponents/dist/Button.js';
import '@ui5/webcomponents/dist/TextArea.js';
import '@ui5/webcomponents/dist/Input.js';
import '@ui5/webcomponents/dist/BusyIndicator.js';
import '@ui5/webcomponents/dist/MessageStrip.js';
import '@ui5/webcomponents/dist/Title.js';
import '@ui5/webcomponents-icons/dist/delete.js';

import { bootstrapApplication } from '@angular/platform-browser';
import { appConfig } from './app/app.config';
import { AppComponent } from './app/app.component';

bootstrapApplication(AppComponent, appConfig).catch((err) => console.error(err));
