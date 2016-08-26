% example: matlab -nodesktop -nojvm -nosplash -r "mabonlm3D_nifti('/Users/atucholka_fpmaragall/Projects/Denoising/SANLM3D/testing/t1.nii','mabonlm')"

 fname = '$source';
 outputext = '$outputext';
 [pathname,filename,ext] = fileparts(fname);
 V = spm_vol(fname);
 ima = spm_read_vols(V);
 %fimau=MABONLM3D(ima,3,1,1);
 fimao=MABONLM3D(ima,3,2,1);
 %fima2=mixingsubband(fimau,fimao);
 fname2 = strcat(pathname, '/',filename, '_', outputext, ext);
 disp(fname2);
 V.fname = fname2;
 spm_write_vol(V, fimao);
 disp(V.fname);
 %exit;

