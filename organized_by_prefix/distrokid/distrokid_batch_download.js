const uuids = [
  'E051DFE5-BE55-4FAD-9682CACF99AFC88E', // Raj
  'DDCB2E62-2DC5-4FE4-83B66329A29026D8', // The Moonlit Sunrise
  'EA46364B-5992-4D2C-B81852BD39A35214'  // The Early Years
];

(async () => {
  const results = [];
  for (const id of uuids) {
    const url = `https://distrokid.com/dashboard/album/?albumuuid=${id}`;
    location.href = url;
    await new Promise(r => setTimeout(r, 3500));
    const links = [...document.querySelectorAll('a[href*="/vault/download/"]')];
    links.forEach((a, i) => setTimeout(() => a.click(), i * 2200));
    results.push({ albumuuid: id, downloadsFound: links.length });
    await new Promise(r => setTimeout(r, Math.max(5000, links.length * 2300)));
  }
  return results;
})();