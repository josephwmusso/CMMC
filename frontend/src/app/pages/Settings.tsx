import { CheckCircle, AlertCircle, Shield, Database, Network, Cpu, Loader2, Download } from 'lucide-react';
import { useState, useEffect } from 'react';
import { getHealth, verifyAuditChain, generateManifest, downloadManifest, getComplianceOverview, getCompanyProfile } from '../api/client';

export function Settings() {
  const [healthStatus, setHealthStatus] = useState<'checking' | 'healthy' | 'unreachable'>('checking');
  const [healthVersion, setHealthVersion] = useState('');
  const [auditResult, setAuditResult] = useState<any>(null);
  const [auditLoading, setAuditLoading] = useState(false);
  const [manifestLoading, setManifestLoading] = useState(false);
  const [manifestResult, setManifestResult] = useState<any>(null);
  const [orgInfo, setOrgInfo] = useState<any>({});
  const [controlCount, setControlCount] = useState(110);

  useEffect(() => {
    getHealth()
      .then(d => { setHealthStatus('healthy'); setHealthVersion(d.version || ''); })
      .catch(() => setHealthStatus('unreachable'));
    getComplianceOverview()
      .then(d => { setControlCount(d.sprs?.total || 110); setOrgInfo(prev => ({ ...prev, score: d.sprs?.score })); })
      .catch(() => {});
    getCompanyProfile()
      .then(d => setOrgInfo(prev => ({ ...prev, company_name: d.company_name, employee_count: d.employee_count, primary_location: d.primary_location })))
      .catch(() => {});
  }, []);

  const handleVerifyAudit = async () => {
    setAuditLoading(true);
    try { setAuditResult(await verifyAuditChain()); }
    catch (e: any) { setAuditResult({ error: e.message }); }
    finally { setAuditLoading(false); }
  };

  const handleGenerateManifest = async () => {
    setManifestLoading(true);
    try { setManifestResult(await generateManifest()); }
    catch (e: any) { setManifestResult({ error: e.message }); }
    finally { setManifestLoading(false); }
  };

  const services = [
    { name: 'FastAPI Backend', port: 8001, icon: Cpu },
    { name: 'PostgreSQL', port: 5432, icon: Database },
    { name: 'Qdrant Vector Store', port: 6333, icon: Network },
    { name: 'Temporal Workflow', port: 7233, icon: Shield },
  ];

  return (
    <div className="p-6 w-full">
      <div className="mb-8">
        <h1 className="text-xl font-medium text-zinc-100 mb-1">Settings</h1>
        <p className="text-sm text-zinc-500">System health, audit integrity, and platform info</p>
      </div>

      {/* System Health */}
      <div className="mb-8">
        <h2 className="text-sm font-medium text-zinc-400 mb-4 uppercase tracking-wider">System Health</h2>
        <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl overflow-hidden divide-y divide-zinc-800">
          {services.map(svc => (
            <div key={svc.name} className="flex items-center justify-between px-6 py-4">
              <div className="flex items-center gap-3">
                <svc.icon className="w-4 h-4 text-zinc-500" />
                <span className="text-sm text-zinc-300">{svc.name}</span>
                <span className="text-xs text-zinc-600">:{svc.port}</span>
              </div>
              {healthStatus === 'checking' ? (
                <Loader2 className="w-4 h-4 text-zinc-500 animate-spin" />
              ) : healthStatus === 'healthy' ? (
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-emerald-500" />
                  <span className="text-xs text-emerald-400">Online</span>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-red-500" />
                  <span className="text-xs text-red-400">Unreachable</span>
                </div>
              )}
            </div>
          ))}
        </div>
        {healthVersion && <div className="mt-2 text-xs text-zinc-600">Backend version: {healthVersion}</div>}
      </div>

      {/* Audit Chain */}
      <div className="mb-8">
        <h2 className="text-sm font-medium text-zinc-400 mb-4 uppercase tracking-wider">Audit Chain Integrity</h2>
        <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-6">
          <p className="text-sm text-zinc-500 mb-4">Verify the SHA-256 hash chain integrity of all audit log entries.</p>
          <button onClick={handleVerifyAudit} disabled={auditLoading}
            className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-sm font-medium text-zinc-300 transition-colors flex items-center gap-2">
            {auditLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Shield className="w-4 h-4" />}
            {auditLoading ? 'Verifying...' : 'Verify Audit Chain'}
          </button>
          {auditResult && !auditResult.error && (
            <div className="mt-4 flex items-center gap-3">
              {auditResult.valid ? (
                <><CheckCircle className="w-5 h-5 text-emerald-400" /><span className="text-sm text-emerald-400">Chain intact — {auditResult.entries_checked} entries verified</span></>
              ) : (
                <><AlertCircle className="w-5 h-5 text-red-400" /><span className="text-sm text-red-400">Chain broken at entry {auditResult.first_broken}</span></>
              )}
            </div>
          )}
          {auditResult?.error && <p className="mt-4 text-sm text-red-400">{auditResult.error}</p>}
        </div>
      </div>

      {/* Hash Manifest */}
      <div className="mb-8">
        <h2 className="text-sm font-medium text-zinc-400 mb-4 uppercase tracking-wider">Evidence Hash Manifest</h2>
        <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-6">
          <p className="text-sm text-zinc-500 mb-4">Generate a SHA-256 hash manifest for all evidence artifacts.</p>
          <div className="flex items-center gap-3">
            <button onClick={handleGenerateManifest} disabled={manifestLoading}
              className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-sm font-medium text-zinc-300 transition-colors flex items-center gap-2">
              {manifestLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Shield className="w-4 h-4" />}
              {manifestLoading ? 'Generating...' : 'Generate Manifest'}
            </button>
            {manifestResult && !manifestResult.error && (
              <button onClick={downloadManifest} className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-sm text-zinc-300 flex items-center gap-2">
                <Download className="w-4 h-4" /> Download
              </button>
            )}
          </div>
          {manifestResult && !manifestResult.error && (
            <div className="mt-4 text-sm text-zinc-400">{manifestResult.artifact_count} artifacts hashed</div>
          )}
          {manifestResult?.error && <p className="mt-4 text-sm text-red-400">{manifestResult.error}</p>}
        </div>
      </div>

      {/* Platform Info */}
      <div className="mb-8">
        <h2 className="text-sm font-medium text-zinc-400 mb-4 uppercase tracking-wider">Platform Info</h2>
        <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl overflow-hidden divide-y divide-zinc-800">
          {[
            ['Organization', orgInfo.company_name || 'Apex Defense Solutions'],
            ['Employees', orgInfo.employee_count ? String(orgInfo.employee_count) : '—'],
            ['Location', orgInfo.primary_location || '—'],
            ['Framework', 'CMMC Level 2 (NIST 800-171 Rev 2)'],
            ['Controls', String(controlCount)],
            ['SPRS Score', orgInfo.score !== undefined ? String(orgInfo.score) : '—'],
            ['Version', healthVersion || '0.9.0'],
          ].map(([label, value]) => (
            <div key={label} className="flex items-center justify-between px-6 py-3">
              <span className="text-sm text-zinc-500">{label}</span>
              <span className="text-sm text-zinc-300 font-mono">{value}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
