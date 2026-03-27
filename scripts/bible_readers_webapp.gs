const SHEET_NAME = 'Sheet1';
const HEADER_DRIVE_FILE_ID = '1IbF338LNsmcLmnmbCxN96t4rYwUdHhFQ';
const OWNER_NOTIFICATION_EMAIL = 'ryan.vegh@gmail.com';

function doGet() {
  const slots = getAvailableSlots_();
  const t = HtmlService.createTemplateFromFile('index');
  const header = getHeaderSources_();
  t.payload = {
    generatedAt: new Date().toISOString(),
    slots,
    headerUrl: header.headerUrl,
    headerDataUrl: header.headerDataUrl,
  };
  return t.evaluate()
    .setTitle('8:1 Bible Readers Signup');
}

function getHeaderSources_() {
  const headerUrl = `https://lh3.googleusercontent.com/d/${HEADER_DRIVE_FILE_ID}=w1600`;
  let headerDataUrl = '';
  try {
    const file = DriveApp.getFileById(HEADER_DRIVE_FILE_ID);
    const blob = file.getBlob();
    // Keep payload reasonable for mobile by relying on original JPEG compression.
    const b64 = Utilities.base64Encode(blob.getBytes());
    headerDataUrl = `data:${blob.getContentType()};base64,${b64}`;
  } catch (err) {
    // Fallback to public thumbnail URL if Drive server-side fetch fails.
  }
  return { headerUrl, headerDataUrl };
}

function getAvailableSlots_() {
  const sh = SpreadsheetApp.getActive().getSheetByName(SHEET_NAME);
  if (!sh) throw new Error(`Missing sheet: ${SHEET_NAME}`);

  const lastRow = sh.getLastRow();
  const range = sh.getRange(1, 1, lastRow, 4); // A:D
  const values = range.getValues();
  const display = range.getDisplayValues();

  const slots = [];
  let section = '';

  for (let r = 0; r < values.length; r++) {
    const rowNumber = r + 1;
    const label = String(display[r][0] || '').trim();
    const first = String(display[r][1] || '').trim();
    const last = String(display[r][2] || '').trim();
    const phone = String(display[r][3] || '').trim();

    if (!label) continue;

    const isSectionHeader = /\s-\s/.test(label) && /First Name/i.test(String(display[r][1] || ''));
    if (isSectionHeader) {
      section = label;
      continue;
    }

    const looksLikeSlot = /^(?:\d{1,2}:\d{2}\s*(?:AM|PM)|NOON|Revelation\s+\d+)$/i.test(label);
    if (!looksLikeSlot) continue;

    const taken = !!(first || last || phone);
    if (!taken) {
      slots.push({
        row: rowNumber,
        section,
        label,
        kind: /^Revelation\s+/i.test(label) ? 'chapter' : 'timeslot',
      });
    }
  }

  return slots;
}

function submitSignup(form) {
  const row = Number(form.row);
  const firstName = String(form.firstName || '').trim();
  const lastName = String(form.lastName || '').trim();
  const phone = String(form.phone || '').trim();

  if (!row || !firstName || !lastName || !phone) {
    throw new Error('Missing required fields.');
  }

  const lock = LockService.getDocumentLock();
  lock.waitLock(30000);
  try {
    const sh = SpreadsheetApp.getActive().getSheetByName(SHEET_NAME);
    const slotLabel = String(sh.getRange(row, 1).getValue() || '').trim();
    const current = sh.getRange(row, 2, 1, 3).getValues()[0];
    const alreadyTaken = current.some(v => String(v || '').trim() !== '');

    if (alreadyTaken) {
      return { ok: false, message: `Sorry, ${slotLabel} was just taken. Please choose another slot.` };
    }

    sh.getRange(row, 2, 1, 3).setValues([[firstName, lastName, phone]]);

    // Owner notification for each successful signup.
    try {
      const sectionLabel = String(sh.getRange(row, 1).offset(0, -0).getValue() || '').trim();
      const subject = `Bible Readers signup: ${firstName} ${lastName} @ ${slotLabel}`;
      const body = [
        'A new Bible Readers signup was submitted.',
        '',
        `Name: ${firstName} ${lastName}`,
        `Phone: ${phone}`,
        `Slot: ${slotLabel}`,
        `Row: ${row}`,
        `Sheet: ${SHEET_NAME}`,
      ].join('\n');
      MailApp.sendEmail(OWNER_NOTIFICATION_EMAIL, subject, body);
    } catch (err) {
      // Do not block signup if notification email fails.
      console.error('Owner notification email failed:', err);
    }

    return { ok: true, message: `You’re signed up for ${slotLabel}.`, slotLabel };
  } finally {
    lock.releaseLock();
  }
}
