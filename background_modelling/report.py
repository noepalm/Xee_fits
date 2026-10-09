import argparse
import re
import sys
from pathlib import Path

def parse_log(log_path: Path):
    if not log_path.exists():
        print(f"❌ File not found: {log_path.name}")
        return

    boundary_params = {}
    final_chi2 = "N/A"
    final_ndf = "N/A"
    fit_status = "UNKNOWN"
    res_chi2 = {}
    
    # Iteration tracking
    iterations_run = 0
    max_iterations = 0
    converged = False

    # Regex definitions matching your log output
    re_boundary = re.compile(r"^\s*([a-zA-Z0-9_]+):\s+[-.\deE]+\s+±.*?BOUNDARY WARNING")
    re_final_chi2 = re.compile(r"^\s*Chi2 for full_bkg_model:\s+([0-9.]+)\s+\(n\. free params =\s+(\d+)\)")
    re_res_chi2 = re.compile(r"^([a-zA-Z0-9_]+)\s+chi2\s*=\s*([0-9.]+)\s+\(n\. free params =\s+(\d+)\)")
    re_status = re.compile(r"^\s*Fit status:\s+(-?\d+)")
    
    # Custom regexes for the iterative loop (ignores RooFit MINUIT outputs)
    re_iteration = re.compile(r"^\s*\[Iteration\s+(\d+)/(\d+)\]")
    re_convergence = re.compile(r"^\s*Convergence reached at iteration\s+(\d+)\.")

    with open(log_path, 'r') as f:
        for line in f:
            # 1. Catch boundary warnings
            m_bound = re_boundary.search(line)
            if m_bound:
                param_name = m_bound.group(1)
                
                # Ignore yield/normalization parameters (ndy, nphi, nomega, etc.)
                if re.match(r"^n(dy|jpsi|psi2s|upsilon1s|upsilon2s|phi|omega|eta)_", param_name):
                    continue
                    
                boundary_params[param_name] = line.strip()
                continue
                
            # 2. Catch final model chi2
            m_final = re_final_chi2.match(line)
            if m_final:
                final_chi2 = m_final.group(1)
                final_ndf = m_final.group(2)
                continue
                
            # 3. Catch prompt resonant chi2
            m_res = re_res_chi2.match(line)
            if m_res:
                res_chi2[m_res.group(1)] = (m_res.group(2), m_res.group(3))
                continue
                
            # 4. Catch final fit status
            m_stat = re_status.match(line)
            if m_stat:
                fit_status = m_stat.group(1)
                continue
                
            # 5. Catch iterations
            m_iter = re_iteration.match(line)
            if m_iter:
                iterations_run = int(m_iter.group(1))
                max_iterations = int(m_iter.group(2))
                continue
                
            # 6. Catch convergence
            m_conv = re_convergence.match(line)
            if m_conv:
                converged = True
                iterations_run = int(m_conv.group(1))
                continue

    # Format the output block
    print(f"\n[{log_path.name}]")
    
    if max_iterations > 0:
        conv_str = "Yes" if converged else "No (Hit Max)"
        print(f"  Iterative Fit: {iterations_run}/{max_iterations} iterations (Converged: {conv_str})")
    
    chi2_number = f"{float(final_chi2):.5f}" if final_chi2 != "N/A" else final_chi2
    print(f"  Final chi2 : {chi2_number} (ndf = {final_ndf}); fit status = {fit_status}")
    
    if res_chi2:
        print("  Resonant Chi2 (Prompt):")
        for res_name, (chi, ndf) in res_chi2.items():
            print(f"    - {res_name}: {chi} (ndf = {ndf})")
            
    if len(boundary_params.keys()) > 0:
        print("  Boundary Warnings:")
        for param_name, warning_line in boundary_params.items():
            print(f"    {warning_line}")
    else:
        print("    None")

def main():
    parser = argparse.ArgumentParser(description="Parse background fit logs and report status.")
    parser.add_argument("--log_dir", required=True, help="Directory containing the logs")
    parser.add_argument("--era", required=True)
    parser.add_argument("--region", required=True)
    parser.add_argument("--model", required=True)
    args = parser.parse_args()

    # Construct the exact filename matching the bash script output
    filename = f"reweight_data_{args.region}_altbkg_{args.model}_allCorrections_{args.era}_binned_log"
    log_path = Path(args.log_dir) / filename

    parse_log(log_path)

if __name__ == "__main__":
    main()