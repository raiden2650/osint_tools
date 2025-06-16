from flask import Flask, render_template, request, send_file, make_response
import pandas as pd
import io
import socket
import dns.resolver

app = Flask(__name__)

# Helper: resolve domain to IPs (one-to-many)
def resolve_domain(domain):
    try:
        answers = dns.resolver.resolve(domain.strip(), 'A')
        return [rdata.to_text() for rdata in answers]
    except Exception:
        return []

# Helper: reverse IP to domains
def reverse_ip(ip):
    try:
        host, aliases, _ = socket.gethostbyaddr(ip.strip())
        return [host] + aliases
    except Exception:
        return []

# Helper: resolve CNAME for a given hostname
def resolve_cname(name):
    try:
        answers = dns.resolver.resolve(name, 'CNAME')
        return [rdata.to_text() for rdata in answers]
    except Exception:
        return []

# Homepage: Domain => IP
@app.route('/', methods=['GET', 'POST'])
def domain_to_ip():
    results = None
    if request.method == 'POST':
        data = request.form['input_data']
        domains = [d for d in data.splitlines() if d.strip()]
        rows = []
        for d in domains:
            ips = resolve_domain(d)
            if ips:
                for ip in ips:
                    rows.append({'Domain': d, 'IP Address': ip})
            else:
                rows.append({'Domain': d, 'IP Address': ''})
        results = pd.DataFrame(rows)
        # Download CSV
        if 'download' in request.form:
            buf = io.StringIO()
            results.to_csv(buf, index=False)
            buf.seek(0)
            resp = make_response(buf.getvalue())
            resp.headers['Content-Disposition'] = 'attachment; filename=domain_to_ip.csv'
            resp.mimetype = 'text/csv'
            return resp
    return render_template('domain_to_ip.html', table=results)

# Subpage: IP => Domain/CNAME
@app.route('/reverse', methods=['GET', 'POST'])
def ip_to_domain():
    results = None
    if request.method == 'POST':
        data = request.form['input_data']
        include_cname = bool(request.form.get('include_cname'))
        ips = [i for i in data.splitlines() if i.strip()]
        rows = []
        for ip in ips:
            hosts = reverse_ip(ip)
            if hosts:
                for h in hosts:
                    rows.append({'IP Address': ip, 'Domain': h, 'CNAME Flag': ''})
                    if include_cname:
                        cnames = resolve_cname(h)
                        for cname in cnames:
                            rows.append({'IP Address': ip, 'Domain': cname, 'CNAME Flag': 'Yes'})
            else:
                # no PTR records
                rows.append({'IP Address': ip, 'Domain': '', 'CNAME Flag': ''})
        results = pd.DataFrame(rows)
        # Download CSV
        if 'download' in request.form:
            buf = io.StringIO()
            results.to_csv(buf, index=False)
            buf.seek(0)
            resp = make_response(buf.getvalue())
            resp.headers['Content-Disposition'] = 'attachment; filename=ip_to_domain.csv'
            resp.mimetype = 'text/csv'
            return resp
    return render_template('ip_to_domain.html', table=results)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
