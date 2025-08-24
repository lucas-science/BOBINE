const ONLINE = 'online';
const OFFLINE = 'offline';

const PIGNA =  'pigna';
const CONTEXT = 'context';


export const FILE_ZONE = {
  context: [{ zone: CONTEXT, max_files: 1 }],
  pigna: [{ zone: PIGNA,    max_files: 1 }],
  chromeleon: [
    { zone: ONLINE,  max_files: 1 },
    { zone: OFFLINE, max_files: 2 },
  ],
} as const;